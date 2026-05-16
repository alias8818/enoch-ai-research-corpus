# Firmware Diff Explainer: A Lightweight Deterministic Tool for First-Pass Firmware Rootfs Diff Triage

> **AI Provenance Notice:** This draft was generated entirely by an AI system from automated research artifacts (run notes, decision JSON, metrics, and log files). The operator who released these artifacts claims no personal authorship credit for the writing or the results. Readers should treat this document as an unreviewed AI-generated research artifact and exercise appropriate skepticism. No human review is claimed or implied.

---

## Abstract

We present Firmware Diff Explainer, a lightweight, deterministic tool for first-pass triage of differences between firmware or rootfs images. The tool extracts filesystem trees from tar, tar.gz, and SquashFS archives, performs file-level differencing, and produces structured reports annotating added, removed, and modified files together with string-level and ELF import-level change summaries. We evaluate the tool on synthetic firmware images with known ground truth and on a real public firmware pair (OpenWrt 23.05.4 and 23.05.5 x86-64 rootfs tarballs). The synthetic test correctly identifies an added `system` import in a stripped ELF binary and a removed default password string. The OpenWrt validation run processes 936 files per image, reporting 55 added files, 55 removed files, 156 modified files, 225 added strings, and 224 removed strings in 8.31 seconds with 36,340 KB peak RSS. A `readelf` output parser bug discovered during evaluation—causing incomplete import annotations when version-index columns were present—was corrected and the validation rerun. The tool is not a semantic reverse-engineering system; it does not decompile functions or prove exploitability. Its security annotations are regex- and string-based, making it a triage explainer rather than a vulnerability oracle.

## Introduction

Firmware updates are routine in embedded device maintenance, yet understanding what changed between two firmware releases remains a manual and error-prone process. Security analysts, compliance teams, and embedded developers frequently need to determine what changed between firmware version A and version B, and whether any of those changes are security-relevant.

Existing approaches to firmware diffing span a range from simple binary diffing to full symbolic execution and decompilation frameworks. A gap exists between trivial directory-level comparisons—which require pre-extracted filesystems and produce unstructured output—and heavyweight reverse-engineering toolchains—which require significant expertise and computational resources. This gap is particularly relevant for first-pass triage, where the goal is to rapidly identify candidate changes worth deeper investigation rather than to prove the presence or absence of vulnerabilities.

We describe Firmware Diff Explainer, a Python-based tool designed to occupy this gap. It accepts firmware rootfs images in common archive formats, extracts them deterministically, performs multi-level differencing (file presence, file content, embedded strings, ELF imports), and produces both human-readable Markdown reports and machine-readable JSON metrics. The tool deliberately avoids semantic analysis, decompilation, and network-dependent enrichment, trading depth for determinism, auditability, and minimal dependencies.

This paper documents the design, implementation, and evaluation of the tool, including both synthetic tests with known ground truth and validation against public OpenWrt firmware releases. We report results honestly, including a parser bug discovered during testing, limitations of the string-based approach, and areas where the tool produces incomplete or potentially noisy annotations.

## Method

### Design Principles

The tool was designed around three principles:

1. **Determinism.** Given the same pair of input images, the tool must produce identical output regardless of the host environment. It requires no network access and employs no non-deterministic heuristics.
2. **Minimal dependencies.** The tool relies only on standard Linux firmware analysis tools (`file`, `strings`, `readelf`, `objdump`, `unsquashfs`, `gzip`, `sha256sum`) and Python 3.12 standard library modules.
3. **Multi-level annotation.** Rather than reporting only file-level differences, the tool annotates changes at the string level (added/removed strings in modified files) and the ELF import level (added/removed dynamic imports in modified ELF binaries).

### Extraction Pipeline

The tool supports two extraction modes via the `--auto-extract` flag:

- **SquashFS extraction:** Invokes `unsquashfs` on the provided image path.
- **tar/tar.gz extraction:** Decompresses (if gzip) and extracts the archive, with a path traversal guard that rejects archive members whose resolved paths escape the extraction root.

For images that are already extracted directory trees, the tool operates directly on the filesystem without extraction.

### Differencing Pipeline

The differencing pipeline operates in three stages:

1. **File inventory.** Walk both directory trees, compute SHA-256 hashes for every regular file, and classify files as added, removed, unchanged, or modified (same relative path, different hash).
2. **String-level diff.** For each modified file, extract printable strings using the `strings` utility and compute set differences to identify added and removed strings.
3. **ELF import diff.** For each modified file identified as ELF by the `file` utility, parse `readelf --dyn-syms` or `readelf -d` output to extract imported symbol names, and compute set differences of import sets.

### Security-Relevance Heuristics

The tool applies simple regex-based heuristics to flag potentially security-relevant changes, such as added imports of `system`, `execve`, or `popen`, and removed strings matching common default password patterns. These heuristics are explicitly triage-level annotations and should not be treated as vulnerability findings.

### Implementation

The prototype is implemented in a single Python file (`tools/firmware_diff_explainer.py`) that compiles cleanly under `py_compile`. A separate validation script (`tools/validate_results.py`) encodes assertion checks for both synthetic and real firmware test results.

### Test Environment

All experiments were conducted on the following platform:

- **OS:** Linux gx10-efe8 6.17.0-1014-nvidia (Ubuntu), aarch64
- **Python:** 3.12.3
- **Memory available:** 122,397,284 kB (no swap configured)

The available memory far exceeds the tool's requirements; the relevance of the resource metrics reported below is that they establish a low ceiling rather than that the tool was resource-constrained.

## Results

### Synthetic Smoke Test

Two toy firmware filesystem trees were constructed, containing stripped ELF binaries with known differences. A SquashFS image pair was also constructed from the toy trees.

**Directory diff results:**

| Metric | Value |
|---|---|
| Added files | 1 |
| Modified files | 3 |
| Detected added `system` import | Yes |
| Detected removed default password | Yes |

The synthetic test correctly identified:

- An added `system` import in `usr/bin/agent` (a stripped ELF binary where the newer version gained a `system` libc import).
- A removed default password string from a configuration file.

Both findings match the ground truth encoded in the synthetic test data. The synthetic assertions passed.

**SquashFS diff results:** The tool's `--auto-extract` SquashFS path successfully extracted both toy SquashFS images and produced results consistent with the directory diff, confirming that the extraction pipeline preserves file identity across archive and directory modes. These results are from toy images only and do not constitute validation on real vendor SquashFS images with non-trivial offset layouts.

### Parser Bug and Fix

During initial testing, the `readelf` import parser failed to handle version-index columns in ELF dynamic symbol tables, causing some import entries to be missed or misparsed. The parser was corrected to account for version-index formatting, and the synthetic ELF test subsequently reported the expected added `system` import. The OpenWrt validation was rerun after the fix. This bug is reported honestly as a defect discovered during evaluation: the initial OpenWrt run (elapsed_s=7.94, maxrss_kb=36540) produced incomplete import annotations, and only the post-fix run (elapsed_s=8.31, maxrss_kb=36340) should be considered valid for import-level results.

### OpenWrt Public Firmware Validation

Real-world validation was performed using official OpenWrt 23.05.4 and 23.05.5 x86-64 rootfs tarballs downloaded from `downloads.openwrt.org`. SHA-256 checksums were recorded:

```
11eb5baedf16b56e8ba59419b502da7866cf7329372730cbc63a559aa99da710  openwrt-23.05.4-x86-64-rootfs.tar.gz
383311300e1fd796f5a39bf09ad87bcedec61a7f09263f79cd1352757a3573a9  openwrt-23.05.5-x86-64-rootfs.tar.gz
```

**Diff counts (post-parser-fix run):**

| Metric | Value |
|---|---|
| Old file count | 936 |
| New file count | 936 |
| Added files | 55 |
| Removed files | 55 |
| Modified files | 156 |
| Added strings | 225 |
| Removed strings | 224 |

The symmetric file counts (936 in each image, 55 added and 55 removed) are consistent with a release update where files are replaced or relocated rather than simply added or removed. The 156 modified files represent files present in both images at the same relative path but with different content hashes. We have not independently verified these counts against a separate diffing tool; they reflect the output of the prototype under test.

**Resource usage (post-parser-fix run):**

| Metric | Value |
|---|---|
| Elapsed time | 8.31 s |
| Peak RSS | 36,340 KB |

The tool processed both ~936-file rootfs images in under 9 seconds with modest memory consumption (approximately 36 MB RSS), suggesting feasibility for first-pass triage even on resource-constrained workstations. However, this result applies only to images of this scale; scaling behavior for significantly larger firmware images has not been tested.

### Validation Assertions

Both synthetic and real firmware assertion suites passed:

- `synthetic_assertions`: pass
- `real_assertions`: pass

The validation script (`tools/validate_results.py`) and final file manifest were verified, and `py_compile` passed for both the prototype and validation script.

## Limitations

The following limitations are acknowledged:

1. **Not semantic reverse engineering.** The tool does not decompile functions, reconstruct control flow, or prove exploitability. A file flagged as having an added `system` import may use it safely, and a file with no flagged imports may contain vulnerabilities introduced through inline assembly or indirect calls.

2. **Limited extraction coverage.** Filesystem extraction currently covers tar, tar.gz, and pure SquashFS images. Many vendor firmware images use combined container formats (e.g., U-Boot images with appended SquashFS at non-zero offsets, TRX containers, or vendor-specific packaging). These require offset-aware extraction or deeper binwalk integration, which is not yet implemented.

3. **String-based security annotations are triage-level only.** Security relevance is determined by regex and string/import matching. This approach produces both false positives (flagging benign changes) and false negatives (missing changes that are security-relevant but do not manifest as obvious string or import differences). The tool is a triage explainer, not a vulnerability oracle.

4. **No package manifest integration.** The tool operates at the raw filesystem level and does not parse package manager manifests (opkg, apk, dpkg, rpm). Consequently, version deltas for individual packages are not summarized; the user must infer package-level changes from the file-level diff.

5. **No CVE or advisory enrichment.** The tool does not cross-reference detected changes against vulnerability databases or security advisories, as this would require network access or a local advisory database, violating the determinism principle.

6. **Single-platform validation.** Real firmware validation was performed only on OpenWrt x86-64 rootfs tarballs. Behavior on other architectures (MIPS, ARM), other firmware formats, or significantly larger images has not been tested.

7. **String diff noise.** The 225 added and 224 removed strings across 156 modified files in the OpenWrt test include both meaningful changes (e.g., version strings, configuration changes) and noise (e.g., build timestamp strings, auto-generated identifiers). The tool does not currently filter or rank string changes by likely relevance, so the analyst must manually separate signal from noise.

8. **Parser fragility.** The `readelf` output parser required a bug fix during evaluation to handle version-index columns. This suggests that parsing `readelf` output across different toolchain versions or ELF variants may surface further parsing edge cases.

9. **No independent cross-validation of diff counts.** The OpenWrt diff counts (55 added, 55 removed, 156 modified) are reported by the tool itself and have not been independently verified against a separate diffing implementation. Systematic over- or under-counting cannot be ruled out without such cross-validation.

## Reproducibility Checklist

- [x] **Source code available:** `tools/firmware_diff_explainer.py` (single-file Python prototype)
- [x] **Validation script available:** `tools/validate_results.py`
- [x] **Input data identified:** OpenWrt 23.05.4 and 23.05.5 x86-64 rootfs tarballs from `https://downloads.openwrt.org/releases/{23.05.4,23.05.5}/targets/x86/64/`
- [x] **Input checksums recorded:** SHA-256 hashes in `artifacts/logs/openwrt_sha256.txt`
- [x] **Output reports preserved:** `reports/openwrt_23_05_4_to_23_05_5_report.md`, `reports/synthetic_dir_report.md`
- [x] **Output metrics preserved:** `reports/openwrt_23_05_4_to_23_05_5_metrics.json`, `reports/synthetic_dir_metrics.json`
- [x] **Run logs preserved:** `artifacts/logs/openwrt_real_run.log`, `artifacts/logs/synthetic_dir_run.log`, `artifacts/logs/synthetic_squashfs_run.log`
- [x] **Resource metrics recorded:** `artifacts/logs/openwrt_real_time_metrics.txt` (elapsed_s=8.31, maxrss_kb=36340)
- [x] **Platform documented:** Linux aarch64, Python 3.12.3, kernel 6.17.0-1014-nvidia
- [x] **Tool dependencies documented:** `file`, `strings`, `readelf`, `objdump`, `unsquashfs`, `gzip`, `sha256sum`
- [x] **Final file manifest recorded:** `artifacts/logs/final_file_manifest.txt`
- [x] **Compilation check passed:** `py_compile` on both prototype and validation script
- [x] **Assertion checks passed:** Synthetic and real firmware validation suites

## Conclusion

Firmware Diff Explainer demonstrates that a lightweight, deterministic, first-pass firmware rootfs diff tool is viable for triage purposes. On synthetic test data with known ground truth, the tool correctly identifies added ELF imports and removed default password strings. On real public firmware (OpenWrt 23.05.4 to 23.05.5), the tool produces a structured summary of 55 added files, 55 removed files, 156 modified files, and associated string-level and import-level changes in 8.31 seconds with modest memory usage.

The tool's value is bounded by its deliberate design trade-offs: it performs string- and import-level annotation rather than semantic analysis, it covers only a subset of firmware archive formats, and its security-relevance heuristics are prone to both false positives and false negatives. A parser bug discovered during evaluation further underscores that the tool's `readelf` output parsing may be fragile across toolchain versions. These limitations are inherent to the triage-first design and are not addressed by the current implementation.

Plausible next steps include offset-aware extraction for combined vendor images, package manifest parsers for cleaner version-delta summaries, and optional CVE enrichment when a local advisory database is available. Each of these extensions would increase coverage at the cost of additional complexity and potential non-determinism, and should be evaluated against the tool's core principle of deterministic reproducibility.

---

## Referenced Artifacts

| Artifact | Path |
|---|---|
| Prototype source | `tools/firmware_diff_explainer.py` |
| Validation script | `tools/validate_results.py` |
| Run notes | `run_notes.md` |
| Project decision | `.omx/project_decision.json` |
| Session metrics | `.omx/metrics.json` |
| Claim ledger | `papers/source-record-redacted-20260502T160918586456+0000/claim_ledger.json` |
| Evidence bundle | `papers/source-record-redacted-20260502T160918586456+0000/evidence_bundle.json` |
| Paper manifest | `papers/source-record-redacted-20260502T160918586456+0000/paper_manifest.json` |
| Synthetic directory report | `reports/synthetic_dir_report.md` |
| Synthetic SquashFS report | `reports/synthetic_squashfs_extracted_report.md` |
| OpenWrt diff report | `reports/openwrt_23_05_4_to_23_05_5_report.md` |
| Synthetic directory metrics | `reports/synthetic_dir_metrics.json` |
| OpenWrt diff metrics | `reports/openwrt_23_05_4_to_23_05_5_metrics.json` |
| OpenWrt SHA-256 log | `artifacts/logs/openwrt_sha256.txt` |
| OpenWrt run log | `artifacts/logs/openwrt_real_run.log` |
| OpenWrt time metrics | `artifacts/logs/openwrt_real_time_metrics.txt` |
| Synthetic directory run log | `artifacts/logs/synthetic_dir_run.log` |
| Synthetic SquashFS run log | `artifacts/logs/synthetic_squashfs_run.log` |
| Validation log | `artifacts/logs/validation.log` |
| Final file manifest | `artifacts/logs/final_file_manifest.txt` |
| Project README | `README.md` |
