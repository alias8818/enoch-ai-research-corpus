# Public FastAPI–Typer Compatibility Oracle Validation

> **AI provenance notice.** This draft was AI-generated from automated research artifacts (run notes, decision JSON, evidence bundles, and result files). The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human review is asserted or implied.

---

## Abstract

We describe a small, reproducible compatibility oracle that tests whether given combinations of FastAPI, Typer, and Click are mutually compatible for CLI help-rendering paths. The oracle exercises three checks—FastAPI import and route registration, Typer CLI invocation via `typer.testing.CliRunner`, and Typer `--help` rendering—and supplements these with a real `fastapi --help` entrypoint check. Across seven isolated virtual-environment configurations, the oracle correctly discriminates between compatible and incompatible version pairs. The known incompatibility between Typer `<0.16.0` and Click `>=8.2.0`, arising from a `make_metavar` signature change introduced in Click 8.2, is reproduced in both the minimal oracle and the real CLI. Current public `fastapi[standard]` installation resolves to compatible versions because `fastapi-cli >=0.0.22` requires `typer >=0.16.0`. The risk is confined to locked or pinned environments that preserve an older Typer while allowing Click to upgrade to `8.2+`. These results are from isolated smoke-test invocations, not sustained production deployments.

## Introduction

FastAPI provides a CLI layer through the `fastapi-cli` package, which depends on Typer, which in turn depends on Click. Click 8.2 introduced a breaking signature change to `Parameter.make_metavar()`, adding a required `ctx` positional argument. Typer versions prior to 0.16.0 did not accommodate this change, producing `TypeError` exceptions when help text was rendered. Typer 0.16.0 added explicit compatibility with Click 8.2.

The practical question is whether current public FastAPI installations are affected and whether a lightweight oracle can reliably detect the incompatibility in arbitrary version combinations. This matters because `fastapi-cli` versions `0.0.8` through `0.0.21` specified only `typer >=0.15.1`, permitting resolution of Typer 0.15.x alongside Click 8.2+. A lockfile or constraint that pins Typer below 0.16.0 while allowing Click to float to 8.2+ would therefore be vulnerable.

This study constructs and evaluates a minimal compatibility oracle, runs it across seven version configurations, and reports the results. The scope is deliberately narrow: we validate the oracle's discriminative power on a targeted set of version pairs, not the full space of possible combinations.

## Method

### Oracle design

The oracle (`scripts/compat_oracle.py`) performs three sequential checks within an isolated `uv`-managed virtual environment:

1. **FastAPI import check.** Import `fastapi`, instantiate `FastAPI()`, and register a `/health` route. This verifies that the core FastAPI stack is functional at the import level.
2. **Typer CLI runner check.** Define a minimal Typer application and invoke it via `typer.testing.CliRunner`. This exercises the Typer/Click command dispatch path.
3. **Typer help-rendering check.** Render `--help` on the Typer application, which exercises Click's metavar and help formatting. This is the specific path that triggers the `make_metavar` incompatibility.

A supplementary check (`scripts/check_fastapi_cli.sh`) invokes the real `fastapi --help` entrypoint when `fastapi-cli` is installed, providing end-to-end validation against the actual CLI surface.

### Test matrix

Seven configurations were tested, each in a freshly created isolated virtual environment:

| Case | Install request | Key resolved versions |
|---|---|---|
| `latest_fastapi_standard` | `fastapi[standard-no-fastapi-cloud-cli]` | fastapi 0.136.1, fastapi-cli 0.0.24, typer 0.25.1, click 8.3.3 |
| `historical_fastapi_cli_0021_resolved_latest` | `fastapi-cli[standard-no-fastapi-cloud-cli]==0.0.21 fastapi click` | fastapi 0.136.1, fastapi-cli 0.0.21, typer 0.25.1, click 8.3.3 |
| `known_bad_typer0153_click820` | `fastapi-cli==0.0.21 fastapi typer==0.15.3 click==8.2.0` | fastapi 0.136.1, fastapi-cli 0.0.21, typer 0.15.3, click 8.2.0 |
| `known_bad_typer0153_click833` | `fastapi-cli==0.0.21 fastapi typer==0.15.3 click==8.3.3` | fastapi 0.136.1, fastapi-cli 0.0.21, typer 0.15.3, click 8.3.3 |
| `old_click_control_typer0153_click818` | `fastapi-cli==0.0.21 fastapi typer==0.15.3 click==8.1.8` | fastapi 0.136.1, fastapi-cli 0.0.21, typer 0.15.3, click 8.1.8 |
| `fixed_typer0160_click820` | `fastapi-cli==0.0.22 fastapi typer==0.16.0 click==8.2.0` | fastapi 0.136.1, fastapi-cli 0.0.22, typer 0.16.0, click 8.2.0 |
| `latest_typer_click_explicit` | `fastapi typer click` | fastapi 0.136.1, typer 0.25.1, click 8.3.3 (no fastapi-cli) |

All installations used `uv` with Python 3.12. PyPI metadata was fetched live on 2026-04-30.

### Reproduction

```bash
./scripts/run_matrix.sh
./scripts/check_fastapi_cli.sh
cat artifacts/results/matrix_summary.jsonl | jq -s .
cat artifacts/results/fastapi_cli_summary.jsonl | jq -s .
```

## Results

### Oracle results

| Case | Oracle result | `fastapi --help` result |
|---|---|---|
| `latest_fastapi_standard` | PASS | PASS |
| `historical_fastapi_cli_0021_resolved_latest` | PASS | PASS |
| `known_bad_typer0153_click820` | FAIL | FAIL |
| `known_bad_typer0153_click833` | FAIL | FAIL |
| `old_click_control_typer0153_click818` | PASS | PASS |
| `fixed_typer0160_click820` | PASS | PASS |
| `latest_typer_click_explicit` | PASS | N/A (no fastapi-cli installed) |

The oracle and the real CLI entrypoint agree on all applicable cases. No case produced a disagreement between the oracle and the real CLI.

### Failure mode

In both failing cases (`typer==0.15.3` with `click>=8.2.0`), the oracle fails at the help-rendering check with:

```
TypeError: TyperArgument.make_metavar() takes 1 positional argument but 2 were given
```

The real `fastapi --help` command exits with status 1 and logs:

```
TypeError: Parameter.make_metavar() missing 1 required positional argument: 'ctx'
```

These errors are consistent with the Click 8.2 signature change to `Parameter.make_metavar()`, which added a required `ctx` parameter that Typer `<0.16.0` does not pass. The two error messages differ in surface form (one reports excess arguments, the other reports a missing argument), which reflects the different call sites in the Typer and Click code paths, but both trace to the same underlying signature mismatch.

### Control and fix validation

- The `old_click_control_typer0153_click818` case (Typer 0.15.3 with Click 8.1.8) passes, confirming that the failure is specific to Click `>=8.2.0` and not an artifact of Typer 0.15.3 itself.
- The `fixed_typer0160_click820` case (Typer 0.16.0 with Click 8.2.0) passes, confirming that Typer 0.16.0 resolves the incompatibility.
- The `historical_fastapi_cli_0021_resolved_latest` case passes because, despite installing `fastapi-cli==0.0.21`, the unconstrained Typer dependency resolves to Typer 0.25.1, which is compatible. This demonstrates that the incompatibility is not inherent to `fastapi-cli==0.0.21` itself but depends on which Typer version the resolver selects.

### Current public installation status

The `latest_fastapi_standard` case confirms that a current `fastapi[standard]` installation resolves to a fully compatible stack: fastapi 0.136.1, fastapi-cli 0.0.24, typer 0.25.1, click 8.3.3. This is expected because `fastapi-cli >=0.0.22` requires `typer >=0.16.0`.

### Edge case: `latest_typer_click_explicit`

This case intentionally omitted `fastapi-cli`, so the `fastapi --help` check was not applicable. The `fastapi` entrypoint raised a `RuntimeError` instructing the user to install `fastapi[standard]`, which is expected behavior for a bare `fastapi` install without the CLI extra, not a compatibility failure. The oracle itself passed all three checks.

### Resource usage

This was a lightweight smoke test: seven isolated virtual-environment installs and short CLI invocations. Memory remained stable throughout (final `MemAvailable`: ~122.6 GB; swap disabled with `SwapTotal: 0 kB`). No GPU or extended computation was involved.

## Limitations

1. **Scope of the oracle.** The oracle tests only import, CLI invocation, and help-rendering paths. It does not exercise the full FastAPI application server, middleware, or request-handling paths. Other incompatibilities may exist that the oracle does not detect.

2. **Version coverage.** Only seven configurations were tested. The boundary between compatible and incompatible Typer versions was not exhaustively probed beyond 0.15.3 (fail) and 0.16.0 (pass). Intermediate Typer versions (e.g., 0.15.4–0.15.x) were not tested and may or may not exhibit the same failure. Similarly, Click versions between 8.1.8 and 8.2.0 were not tested.

3. **Click version boundary.** The incompatibility was confirmed at Click 8.2.0 and 8.3.3 with Typer 0.15.3, and absence of failure was confirmed at Click 8.1.8. The exact Click version at which the `make_metavar` signature changed was not independently verified beyond consulting public Click documentation stating the change occurred in the 8.2 series.

4. **Single Python version.** All tests used Python 3.12. Behavior on other Python versions was not assessed.

5. **No production workload validation.** These are isolated smoke-test invocations, not sustained production deployments. The oracle validates compatibility at the import and CLI level only. It does not address runtime performance, concurrency, or long-running stability under load.

6. **Single execution.** Each configuration was tested once. While the failure mode is deterministic (a signature mismatch that reliably raises `TypeError`), no repeated-trial analysis was performed.

7. **Temporal specificity.** PyPI metadata was fetched on 2026-04-30. Package versions and dependency specifications may change after that date. The compatibility rule reported here applies to the versions tested; future releases may introduce different constraints.

8. **No formal claim audit.** The claim ledger for this run contains no registered claims. The findings are presented as empirical observations from a smoke test, not as formally audit-approved claims.

## Reproducibility Checklist

- [x] **Code available.** Oracle script: `scripts/compat_oracle.py`; CLI check: `scripts/check_fastapi_cli.sh`; matrix runner: `scripts/run_matrix.sh`; PyPI metadata fetcher: `scripts/pypi_metadata.py`; version logic: `scripts/fastapi_cli_versions`.
- [x] **Isolated environments.** Each test case ran in a freshly created `uv` virtual environment with no shared state.
- [x] **Version pinning.** Install requests explicitly pin versions for the known-bad and control cases.
- [x] **Result artifacts.** Per-case JSON results and logs are recorded under `artifacts/results/` and `artifacts/logs/`.
- [x] **Matrix summary.** Aggregated results in `artifacts/results/matrix_summary.jsonl` and `artifacts/results/fastapi_cli_summary.jsonl`.
- [x] **PyPI metadata logs.** `artifacts/logs/pypi_metadata_20260430T222907Z.jsonl` and `artifacts/logs/fastapi_cli_versions_20260430T222918Z.jsonl`.
- [x] **Hardware/environment.** Python 3.12, `uv` package manager, Linux host with ~122 GB available memory, swap disabled.
- [x] **Determinism note.** Results depend on PyPI-resolved versions at the time of execution. Re-running after package updates may yield different resolved versions for unpinned dependencies. The failure mode itself (signature mismatch) is deterministic given the same version pair.

## Conclusion

A small compatibility oracle successfully discriminates between compatible and incompatible FastAPI/Typer/Click version combinations across the seven configurations tested. The key findings are:

- **Current public `fastapi[standard]` is compatible.** The resolver selects `fastapi-cli >=0.0.22`, which requires `typer >=0.16.0`, avoiding the known incompatibility.
- **The incompatibility `typer < 0.16.0` with `click >= 8.2.0` is reproducible.** It manifests as a `TypeError` in `make_metavar` during help rendering, affecting both minimal Typer invocations and the real `fastapi --help` command.
- **The risk is confined to locked or constrained environments.** A lockfile preserving `typer==0.15.3` (permitted by `fastapi-cli <=0.0.21`) while allowing Click to resolve to `8.2+` will encounter this failure. Unconstrained resolution of the same `fastapi-cli` version avoids the problem by selecting a newer Typer.
- **The oracle is viable for CI or pre-deployment checks.** It runs in seconds, requires no GPU or network access beyond initial package installation, and produces a clear pass/fail signal.

The compatibility rule supported by this evidence is: treat `typer < 0.16.0` combined with `click >= 8.2.0` as incompatible for Typer and FastAPI CLI help-rendering paths. This rule is supported by the specific version pairs tested here; it has not been validated against the full space of intermediate versions.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260430T222818407069+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260430T222818407069+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260430T222818407069+0000/paper_manifest.json` |
| Matrix summary | `artifacts/results/matrix_summary.jsonl` |
| FastAPI CLI summary | `artifacts/results/fastapi_cli_summary.jsonl` |
| PyPI metadata log | `artifacts/logs/pypi_metadata_20260430T222907Z.jsonl` |
| FastAPI CLI versions log | `artifacts/logs/fastapi_cli_versions_20260430T222918Z.jsonl` |
| Latest FastAPI standard result | `artifacts/results/latest_fastapi_standard.json` |
| Latest FastAPI standard log | `artifacts/logs/latest_fastapi_standard_20260430T223007Z.log` |
| Known bad (Click 8.2.0) result | `artifacts/results/known_bad_typer0153_click820.json` |
| Known bad (Click 8.2.0) log | `artifacts/logs/known_bad_typer0153_click820_20260430T223009Z.log` |
| Known bad (Click 8.3.3) result | `artifacts/results/known_bad_typer0153_click833.json` |
| Known bad (Click 8.3.3) log | `artifacts/logs/known_bad_typer0153_click833_20260430T223009Z.log` |
| Old Click control result | `artifacts/results/old_click_control_typer0153_click818.json` |
| Old Click control log | `artifacts/logs/old_click_control_typer0153_click818_20260430T223010Z.log` |
| Fixed Typer 0.16 result | `artifacts/results/fixed_typer0160_click820.json` |
| Fixed Typer 0.16 log | `artifacts/logs/fixed_typer0160_click820_20260430T223011Z.log` |
| Historical fastapi-cli 0.0.21 result | `artifacts/results/historical_fastapi_cli_0021_resolved_latest.json` |
| Historical fastapi-cli 0.0.21 log | `artifacts/logs/historical_fastapi_cli_0021_resolved_latest_20260430T223008Z.log` |
| Oracle script | `scripts/compat_oracle.py` |
| CLI check script | `scripts/check_fastapi_cli.sh` |
| Matrix runner | `scripts/run_matrix.sh` |
| PyPI metadata script | `scripts/pypi_metadata.py` |

### External sources consulted

- PyPI `fastapi-cli` package page: https://pypi.org/project/fastapi-cli/
- FastAPI CLI release notes: https://github.com/fastapi/fastapi-cli/blob/main/release-notes.md
- Typer 0.16.0 release notes: https://github.com/fastapi/typer/releases/tag/0.16.0
- Click multi-version support documentation: https://click.palletsprojects.com/en/stable/support-multiple-versions/
