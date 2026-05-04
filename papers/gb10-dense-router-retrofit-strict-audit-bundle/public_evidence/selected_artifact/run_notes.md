# Dense Router Retrofit — Run Notes

## Research question
Can a dense transformer MLP be retrofitted with an input-dependent router and block-sparse/group-skipping execution so that it preserves the dense-router masked reference while beating the ordinary dense router+MLP path on GB10?

## Lineage and concrete hypothesis
This action starts from two existing local evidence threads:

1. `../34ae3677f1c6816fb2eae1b1c962bcdb` showed a toy/mechanistic result: router-distilled dense masks reduced teacher-MSE by 76.2% vs an equal-parameter dense student, but did not prove inference speed because it still computed the dense hidden activations.
2. `../idea-341e3677f1c681f1b0cbe90b5f0e592b` contained a concrete Triton routed-MLP harness. I copied the executable harness into this project and reran it locally so this project has its own artifacts.

The retrofit tested here is: compute actual router logits from hidden states, compact token blocks whose router scores exceed a calibrated threshold, then run Triton block-sparse MLP kernels over only active blocks. Correctness is measured against a masked dense-router reference, not the unmasked dense model.

## Environment / GB10 posture
- Hardware: NVIDIA GB10 visible through `nvidia-smi`.
- Software: Python 3.12.3, PyTorch 2.11.0+cu130, Triton 3.6.0, CUDA 13.0 (`logs/setup_env.log`).
- Swap: disabled (`SwapTotal: 0 kB`) as expected.
- Memory posture: pre/post `MemAvailable` stayed around 121.7-122.1 GB. `/usr/bin/time -v` reported max RSS ~1.40 GB for the router-integrated run and ~1.50 GB for the decoder-layer run. No swaps occurred.

## Files created
- `src/routed_block_mlp_benchmark.py` — Triton block-sparse routed MLP kernels and reference helpers.
- `src/router_integrated_mlp_benchmark.py` — actual-router-logit integration, fused block-list builder, device-side active-count routed MLP, and module boundary.
- `src/decoder_layer_integration_benchmark.py` — Llama-like decoder-layer prefill harness with RMSNorm, causal SDPA, residuals, and swappable dense/routed MLP.
- `requirements.txt` — reproduction dependencies.
- `logs/*.log` — setup, smoke, and benchmark logs with commands and resource posture.
- `results/*` — CSV and JSON benchmark metrics.

## Commands run
Setup:
```bash
uv venv --python /usr/bin/python3 .venv
uv pip install --python .venv/bin/python torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
uv pip install --python .venv/bin/python triton
.venv/bin/python - <<'PY' | tee logs/setup_env.log
import torch, triton
print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available(), 'cuda', torch.version.cuda)
print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')
print('triton', triton.__version__)
PY
```

Small smoke test:
```bash
/usr/bin/time -v .venv/bin/python src/router_integrated_mlp_benchmark.py \
  --out results/smoke_router_integrated \
  --tokens 256 --d-model 128 --hidden 512 --block-tokens 32 \
  --active-fractions 0.25,0.5 \
  --warmup 5 --repeats 10 \
  2>&1 | tee logs/smoke_router_integrated.log
```
Smoke result: correctness passed, fused builder was ~3.18-3.24x faster than PyTorch compaction, but tiny shape overhead dominated and routed module was slower than dense. This is a useful calibration result: do not claim benefits at very small MLP shapes.

Router-integrated main benchmark:
```bash
/usr/bin/time -v .venv/bin/python src/router_integrated_mlp_benchmark.py \
  --out results/router_integrated_parent_keep_bt32 \
  --tokens 1024 --d-model 512 --hidden 2048 --block-tokens 32 \
  --active-fractions 0.3873697916666667,0.4348958333333333,0.41796875 \
  --warmup 20 --repeats 50 \
  2>&1 | tee logs/router_integrated_parent_keep_bt32.log
```

Decoder-layer integration benchmark:
```bash
/usr/bin/time -v .venv/bin/python src/decoder_layer_integration_benchmark.py \
  --out results/decoder_layer_prefill_parent_keep \
  --shapes 1x1024,2x512,4x256,1x2048 \
  --d-model 512 --hidden 2048 --heads 8 --block-tokens 32 \
  --active-fraction 0.41796875 --warmup 10 --repeats 30 \
  2>&1 | tee logs/decoder_layer_prefill_parent_keep.log
```

## Main metrics — actual-router-logit module boundary
Source: `results/router_integrated_parent_keep_bt32/metrics.csv`.

| requested active fraction | realized active blocks | Triton builder median | builder speedup vs PyTorch | fused counted speedup vs dense | module speedup vs dense | correctness | killed |
|---:|---:|---:|---:|---:|---:|---|---|
| 0.3874 | 12/32 | 12.37 us | 3.22x | 1.278x | 1.192x | pass | false |
| 0.4349 | 14/32 | 12.22 us | 3.22x | 1.244x | 1.155x | pass | false |
| 0.4180 | 13/32 | 12.06 us | 3.20x | 1.254x | 1.180x | pass | false |

Interpretation: the fused/router-specialized block-list builder clears the practical integration bar: below 15 us and >3.2x faster than the generic PyTorch logits-to-`nonzero` path. At parent keep rates, the full device-count routed module remains >1.15x faster than dense router+MLP and matches the masked reference.

## Decoder-layer prefill metrics
Source: `results/decoder_layer_prefill_parent_keep/metrics.csv`.

| batch x seq | active blocks | dense MLP median | routed MLP median | MLP speedup | dense layer median | routed layer median | layer speedup | correctness | killed |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 x 1024 | 13/32 | 134.93 us | 115.01 us | 1.173x | 396.45 us | 328.80 us | 1.206x | pass | false |
| 2 x 512 | 13/32 | 134.37 us | 114.21 us | 1.177x | 377.60 us | 310.70 us | 1.215x | pass | false |
| 4 x 256 | 13/32 | 134.42 us | 114.06 us | 1.178x | 370.59 us | 302.32 us | 1.226x | pass | false |
| 1 x 2048 | 27/64 | 302.85 us | 166.66 us | 1.817x | 754.42 us | 603.95 us | 1.249x | pass | false |

Interpretation: the retrofit survives a concrete decoder-layer prefill boundary. Attention/norm/residual work dilutes the MLP gain, but whole-layer latency still improves 1.21-1.25x in these shapes while preserving the masked dense-router reference.

## Decision
`positive_result / viable_for_next_stage`.

Dense-router retrofit is viable at MVP strength on GB10 for medium transformer-MLP shapes. It is not viable as a blanket small-shape optimization: the 256-token, 128-dim smoke test was slower after router/kernel overhead. The next scientific step should be a real model or open MoE/dense checkpoint integration where router thresholds are trained/calibrated on language-model validation loss, not only synthetic random activations.

## Limitations
- The decoder layer is Llama-like and local, not a full Hugging Face checkpoint replacement.
- Correctness target is a masked dense-router reference. It proves the sparse path implements the router policy, not that the policy preserves original model quality.
- Thresholds are calibrated to target active-block fractions on random hidden states; they are not trained on language data.
- Benchmark repeats are shorter than the parent branch's 100-repeat runs, but sufficient for a local action decision because results are consistent and branch kill gates are explicit.
