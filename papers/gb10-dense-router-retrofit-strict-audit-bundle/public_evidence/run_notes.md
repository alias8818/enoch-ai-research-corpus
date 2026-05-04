# Strict-Pass Featured Enoch Artifact Audit Bundle — Run Notes

## Mission
Build one evidence-backed audit bundle for a featured Enoch artifact from the local project corpus and decide whether it passes strict audit gates.

## Selected artifact
- Project: `34ae3677f1c681f2ab27e86c496ca7d9`
- Name: Dense Router Retrofit
- Path: `../34ae3677f1c681f2ab27e86c496ca7d9`
- Reason selected: highest-scoring locally inspectable positive artifact found in the corpus scan, with executable code, GB10 logs, run notes, CSV/JSON metrics, and `.omx/project_decision.json` declaring `positive_result / viable_for_next_stage` with `needs_review=false`.

## Strict audit gates
1. Positive featured candidate: positive decision, viable disposition, no needs-review flag.
2. Required artifact set present: run notes, README, requirements, source, logs, and metric outputs listed by the artifact decision exist.
3. Existing main metrics support the claim: correctness passed, router module speedup >= 1.15x, builder speedup >= 3.0x, decoder-layer speedup >= 1.20x.
4. Negative small-shape calibration is preserved: tiny smoke is correctly reported as overhead-dominated instead of overclaimed.
5. Fresh live smoke executed from the selected artifact code path and exited 0.
6. GB10 memory posture recorded: GB10 present, swap disabled, MemAvailable high, live smoke RSS bounded.

## Commands and log paths
Environment capture:
```bash
mkdir -p audit_bundle logs .omx
{
  date -Iseconds
  uname -a
  nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader,nounits || true
  grep -E 'MemAvailable|SwapTotal|SwapFree' /proc/meminfo
  python3 --version
} | tee logs/audit_environment.log
```

Fresh live smoke:
```bash
/usr/bin/time -v ../34ae3677f1c681f2ab27e86c496ca7d9/.venv/bin/python \
  ../34ae3677f1c681f2ab27e86c496ca7d9/src/router_integrated_mlp_benchmark.py \
  --out audit_bundle/live_smoke_router_integrated \
  --tokens 128 --d-model 64 --hidden 256 --block-tokens 16 \
  --active-fractions 0.25,0.5 --warmup 2 --repeats 3 \
  2>&1 | tee logs/live_smoke_router_integrated.log
```

Audit bundle construction and JSON validation:
```bash
python3 audit_bundle/build_strict_audit.py | tee logs/build_strict_audit.log
cat audit_bundle/strict_audit.json | python3 -m json.tool >/dev/null
cat audit_bundle/manifest.json | python3 -m json.tool >/dev/null
```

## Metrics summary
Source: `audit_bundle/strict_audit.json`.

- `strict_pass`: `true`
- Selected artifact existing metrics:
  - minimum router module speedup: `1.1550070837656352x`
  - minimum router builder speedup vs PyTorch: `3.2015915858585027x`
  - minimum decoder-layer speedup: `1.2057421227103402x`
  - minimum decoder-MLP speedup: `1.173205403018584x`
- Fresh live smoke metrics:
  - rows: `2`
  - correctness: all builder/MLP/counted/module-boundary checks passed
  - minimum builder speedup vs PyTorch: `3.0160919429489983x`
  - small-shape branches intentionally killed for speedup, matching the selected artifact's limitation.
- Resource posture:
  - GPU: `NVIDIA GB10`
  - swap: `SwapTotal: 0 kB`
  - MemAvailable at audit start: `122735844 kB`
  - live smoke max RSS: `1450136 kB`
  - `/usr/bin/time -v` exit status: `0`

## Durable artifacts produced
- `audit_bundle/strict_audit.json` — strict gate results, metrics, hashes, selected artifact identity.
- `audit_bundle/manifest.json` — bundle file list and pass status.
- `audit_bundle/build_strict_audit.py` — reproducible audit builder.
- `audit_bundle/live_smoke_router_integrated/*` — fresh smoke metrics and summaries.
- `audit_bundle/selected_artifact/*` — copied one-stop evidence subset from selected artifact.
- `logs/audit_environment.log` — environment and memory posture.
- `logs/live_smoke_router_integrated.log` — fresh smoke output and resource usage.
- `logs/build_strict_audit.log` — audit-builder output.
- `.omx/project_decision.json` — final decision for this action.

## Decision
Strict pass. The bundle is complete and evidence-backed for a featured Enoch artifact. Scientific closure remains scoped to an artifact audit, not a new proof of the Dense Router Retrofit's language-model quality; the selected artifact itself already records that limitation.
