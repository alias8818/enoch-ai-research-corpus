# Router Upcycling Eliminates Cold-Start Delay in Synthetic MoE Routing: A Local Benchmark on NVIDIA GB10

> **AI Provenance Notice.** This draft was generated entirely by an AI system from automated research artifacts (run notes, benchmark scripts, metric JSON files, and a project decision ledger). The operator who released this artifact claims no personal authorship credit for the writing or the experimental results beyond making the artifacts available. Readers should treat this document as an unreviewed AI-generated research artifact: it has not been vetted by human domain experts, and all claims should be verified against the referenced primary artifacts before reliance.

---

## Abstract

Mixture-of-experts (MoE) models suffer from a router cold-start problem: randomly initialized routers assign tokens near-uniformly, delaying expert specialization. Recent work proposes initializing routers from preceding attention-head representations (router upcycling) or cluster centroids to address this failure mode. We evaluate whether an upcycling-style initialization reduces cold-start delay in a controlled synthetic setting, and whether the router scoring and top-1 selection path runs feasibly on an NVIDIA GB10 GPU. In a synthetic benchmark where expert labels derive from latent linear directions, an aligned upcycled router achieves 0.865 initial accuracy (versus 0.128 for random initialization) and reaches the 0.85 accuracy threshold at step 0, matching a seeded-centroid oracle upper bound. An unrelated upcycle control initialized from non-aligned directions starts at 0.120 accuracy and requires 100 SGD steps to reach threshold, demonstrating that the benefit depends on genuine alignment between reused representations and expert partition structure—not merely on using non-random weights. A CUDA/cuBLAS microbenchmark on GB10 achieves approximately 5.59 M tokens/s for router logits (16,384 tokens × 4,096 hidden × 8 experts) with peak GPU utilization of 96% and maximum power draw of 17.9 W. These results support the router-upcycling mechanism in a synthetic setting and confirm local hardware feasibility of the router scoring path, but do not demonstrate downstream LLM quality or full MoE upcycling performance.

## Introduction

Mixture-of-experts architectures improve model capacity by routing tokens to specialized sub-networks, but the router itself must learn which expert should receive each token. When the router is initialized randomly, early training produces near-uniform assignments—a phenomenon identified as the cold-start problem in MoE upcycling. Two independent lines of work address this: Ran et al. (arXiv:2509.00679) propose initializing routers from preceding attention-head projections so that token–expert alignment is inherited from pre-trained representations, and Chu et al. (arXiv:2604.13508) seed routers from cluster centroids to break expert symmetry.

The present study asks two questions:

1. **Cold-start reduction.** Does an upcycling-style router initialization—where router weights are derived from the same latent directions that generate the expert partition—reduce cold-start delay relative to random initialization, and does the benefit vanish when the initialization is structurally similar but semantically unaligned?

2. **Local hardware feasibility.** Can the router scoring and top-1 selection path execute on an NVIDIA GB10 GPU at throughput relevant to small-scale MoE inference?

Both questions are investigated through self-contained local benchmarks: a Python-based synthetic cold-start experiment and a CUDA/cuBLAS microbenchmark. No real transformer checkpoints, full MoE training runs, or downstream quality evaluations are performed.

## Method

### Synthetic Cold-Start Benchmark

The benchmark (`scripts/benchmark_router_coldstart.py`) generates synthetic hidden states and expert labels as follows:

- **Hidden states.** Token representations of dimension `hidden` are drawn from a Gaussian mixture whose component means are structured latent directions (analogous to attention-head projection directions), plus isotropic noise.
- **Expert labels.** Each token's expert assignment is determined by which latent direction best aligns with its hidden state, producing a linearly separable partition.

Four router initialization strategies are compared:

| Variant | Initialization |
|---|---|
| `random_cold_start` | Small random Gaussian weights (standard cold-start baseline). |
| `upcycled_aligned` | Weights initialized from the same latent directions used to generate the expert partition, modeling the favorable case where preceding attention-head representations contain routing signal. |
| `upcycled_unrelated_control` | Weights initialized from normalized random directions unrelated to the expert partition, controlling for the effect of using non-random weights without genuine alignment. |
| `seeded_centroid_oracle` | Weights derived from a small seed dataset's cluster centroids, providing an upper-bound baseline. |

All routers are linear maps (`hidden × experts`) followed by softmax. Training uses identical SGD with cross-entropy loss across all variants. Reported metrics include initial and final accuracy, initial and final loss, steps to reach 0.85 accuracy, and normalized assignment entropy.

**Calibrated configuration:** 65,536 tokens, hidden dimension 256, 8 experts, 300 SGD steps, batch size 2,048, learning rate 0.1.

### GPU Router Microbenchmark

The CUDA benchmark (`scripts/gpu_router_bench.cu`) measures the throughput of:

1. A matrix multiply: router logits = `tokens × hidden` multiplied by `hidden × experts` (via cuBLAS).
2. A top-1 selection kernel over the resulting logit matrix.

This isolates the router scoring and expert-selection overhead from expert dispatch, expert computation, and full-model inference/training.

**Calibrated configuration:** 16,384 tokens, hidden dimension 4,096, 8 experts, 200 iterations.

### Execution Environment

- **Host:** Linux `gx10-efe8`, kernel 6.17.0-1014-nvidia, `aarch64`.
- **GPU:** NVIDIA GB10, driver 580.159.03, CUDA 13.0.
- **Memory:** Swap intentionally disabled; earlyoom active. `MemAvailable` remained above 116 GiB throughout.
- **Orchestration:** `scripts/run_benchmark.sh` captures system posture, runs smoke tests before calibrated runs, compiles and executes the CUDA benchmark, and samples `nvidia-smi` during GPU execution.

## Results

### Cold-Start Experiment

Table 1 presents the calibrated synthetic results from `metrics/router_coldstart_final.json`.

**Table 1.** Synthetic router cold-start comparison (65,536 tokens, hidden 256, 8 experts, 300 steps).

| Variant | Initial Acc. | Steps to 0.85 | Final Acc. | Initial Loss | Final Loss |
|---|---:|---:|---:|---:|---:|
| random_cold_start | 0.1285 | 100 | 0.8820 | 2.1183 | 0.6059 |
| upcycled_aligned | 0.8646 | 0 | 0.8833 | 1.6398 | 0.5918 |
| upcycled_unrelated_control | 0.1203 | 100 | 0.8828 | 2.1399 | 0.6062 |
| seeded_centroid_oracle | 0.8673 | 0 | 0.8840 | 1.6118 | 0.5909 |

The aligned upcycled router starts at 0.865 accuracy—well above the 0.85 threshold—and reaches the threshold at step 0, matching the seeded-centroid oracle (0.867 initial accuracy, step 0). The random cold-start and unrelated upcycle control both start near chance level (0.128 and 0.120, respectively, for 8 experts where uniform chance is 0.125) and require 100 steps to reach threshold.

The unrelated upcycle control is a critical negative result: initializing from non-random but semantically unaligned directions provides no cold-start benefit over random initialization. The benefit of upcycling depends on genuine alignment between the reused representation and the expert partition structure.

All variants converge to similar final accuracy (0.882–0.884) and final loss (0.591–0.606), indicating that the initialization affects convergence speed but not asymptotic performance in this synthetic regime.

Normalized assignment entropy remained high across all variants (0.999–1.000 at initialization, 0.999 at convergence), reflecting near-uniform expert utilization in this linearly separable synthetic setting. This does not imply that load balance would be maintained in real MoE training with non-linear expert specialization.

### GPU Router Throughput

Table 2 presents the calibrated CUDA results from `metrics/gpu_router_calibrated.json`.

**Table 2.** GB10 router scoring + top-1 throughput (16,384 tokens × 4,096 hidden × 8 experts, 200 iterations).

| Metric | Value |
|---|---|
| Total time | 0.586 s |
| Tokens/s | 5,591,850 |
| Router GFLOPS | 366.5 |
| Device memory | 269.2 MB |
| Peak GPU utilization | 96% |
| Peak power draw | 17.9 W |

The smoke test (2,048 tokens × 1,024 hidden × 8 experts, 20 iterations) completed in 0.54 ms at approximately 75.9 M tokens/s, but the `nvidia-smi` sampler did not capture GPU utilization during this short run. The calibrated run confirmed sustained GB10 execution with measurable GPU utilization (average 32%, peak 96%) and modest power draw.

## Limitations

1. **Synthetic data only.** Expert labels are generated from latent linear directions plus noise, not from a real transformer or MoE checkpoint. The degree to which real attention-head representations contain routing signal for downstream expert partitions is an empirical question that this benchmark does not address.

2. **Favorable alignment assumption.** The aligned upcycled router models the case where preceding attention-head-like directions genuinely encode expert partition structure. The unrelated control demonstrates this assumption is necessary, but real transformers may fall anywhere between the aligned and unrelated conditions.

3. **Linear router, linear partition.** The synthetic task is linearly separable by construction. Real MoE routing involves non-linear expert specialization and token–expert interactions that a linear router may not capture.

4. **No downstream quality evaluation.** Router accuracy on synthetic labels does not measure downstream language modeling loss, perplexity, or task performance.

5. **CUDA microbenchmark scope.** The GPU benchmark covers router logit computation and top-1 selection only. It excludes expert dispatch overhead, expert forward/backward passes, all-to-all communication, and full-model inference or training. The throughput figure (5.59 M tokens/s) characterizes the router scoring path in isolation.

6. **Atypical memory configuration.** The test environment ran with swap disabled and earlyoom active, which is not representative of most production deployments. Memory behavior under swap-enabled configurations was not tested.

7. **Single GPU, single configuration.** Results are specific to the NVIDIA GB10, the tested tensor dimensions, and 8 experts. Scaling to larger hidden dimensions, more experts, or different hardware may yield different throughput and utilization profiles.

8. **Random seed reproducibility.** The synthetic benchmark generates data deterministically from latent directions, but explicit random seed values are not recorded in the metric files. Exact numerical reproducibility may depend on Python and NumPy default seeding behavior.

9. **Claim audit incomplete.** The claim ledger for this paper contains no formally audited claims at time of generation. The paper review checklist records 9 pending items and 0 passed items. Readers should treat all stated results as unaudited.

## Reproducibility Checklist

- [x] **Benchmark scripts included.** `scripts/benchmark_router_coldstart.py` (Python cold-start experiment), `scripts/gpu_router_bench.cu` (CUDA microbenchmark), `scripts/run_benchmark.sh` (orchestration).
- [x] **Command-line arguments documented.** All runs invoked with explicit `--tokens`, `--hidden`, `--experts`, `--steps`, `--batch`, `--lr`, `--threshold`, `--out` flags.
- [x] **Hardware and software environment recorded.** Host architecture, kernel version, GPU model, driver version, CUDA version, swap status, and earlyoom status documented in run notes.
- [x] **Raw metric files preserved.** `metrics/router_coldstart_final.json`, `metrics/gpu_router_calibrated.json`, `metrics/summary.json`, and smoke-test counterparts.
- [x] **GPU telemetry captured.** `logs/nvidia_smi_router_calibrated.csv` (9 samples) and `logs/nvidia_smi_router_smoke.csv` (3 samples).
- [x] **Run log preserved.** `logs/benchmark_20260502T174655.log`.
- [x] **Project decision ledger preserved.** `.omx/project_decision.json` records hypothesis status, confidence, and recommended next action.
- [ ] **Explicit random seed recording.** Not performed; reproducers should verify whether Python and NumPy default seeds produce identical results.
- [ ] **Full MoE training reproduction.** Not applicable; no real MoE training was performed.
- [ ] **Cross-hardware validation.** Not performed; results are specific to the GB10 host described above.
- [ ] **Claim audit completion.** The claim ledger contains zero audited claims; the paper review checklist has 9 pending items and 0 passed items.

## Conclusion

In a controlled synthetic benchmark, router upcycling—initializing MoE router weights from attention-head-like directions that align with the expert partition—eliminates the cold-start delay entirely: the aligned upcycled router starts at 0.865 accuracy and reaches the 0.85 threshold at step 0, matching a seeded-centroid oracle. A structurally similar but semantically unaligned initialization provides no benefit over random initialization, confirming that the mechanism depends on genuine representation–partition alignment rather than merely on non-random weight magnitudes. A CUDA microbenchmark confirms that the router scoring and top-1 selection path runs on the NVIDIA GB10 at approximately 5.59 M tokens/s with peak 96% GPU utilization and 17.9 W power draw.

These findings support the plausibility of the router-upcycling mechanism and the local hardware feasibility of the router scoring path, but they remain bounded by the synthetic, linearly separable setting. The critical next step is a real-model follow-on: extracting hidden activations and attention-head projections from an open transformer, constructing MoE expert partitions from real token/task clusters, and comparing random, attention-head-upcycled, and centroid-seeded routers on downstream validation loss and expert utilization. Until such a study is completed, the present results should be interpreted as mechanism-validation under favorable conditions, not as evidence of downstream MoE quality improvement.

## Referenced Artifacts

All artifacts reside in the project directory `<control-plane-projects>/source-record-redacted`.

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Cold-start benchmark script | `scripts/benchmark_router_coldstart.py` |
| GPU benchmark source | `scripts/gpu_router_bench.cu` |
| Orchestration script | `scripts/run_benchmark.sh` |
| Cold-start smoke metrics | `metrics/router_coldstart_smoke_final.json` |
| Cold-start calibrated metrics | `metrics/router_coldstart_final.json` |
| GPU smoke metrics | `metrics/gpu_router_smoke.json` |
| GPU calibrated metrics | `metrics/gpu_router_calibrated.json` |
| Summary metrics | `metrics/summary.json` |
| Main run log | `logs/benchmark_20260502T174655.log` |
| GPU telemetry (smoke) | `logs/nvidia_smi_router_smoke.csv` |
| GPU telemetry (calibrated) | `logs/nvidia_smi_router_calibrated.csv` |
| Project decision ledger | `.omx/project_decision.json` |
| Claim ledger | `papers/source-record-redacted-20260502T224304346310+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T224304346310+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T224304346310+0000/paper_manifest.json` |

External references consulted:

- Ran et al., arXiv:2509.00679. https://arxiv.org/abs/2509.00679
- Chu et al., arXiv:2604.13508. https://arxiv.org/abs/2604.13508
