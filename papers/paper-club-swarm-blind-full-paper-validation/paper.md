# Blind Multi-Role Paper-Club Swarm for Automated Review Artifact Generation: A Prototype Validation

> **AI Provenance Notice:** This draft was AI-generated from automated research artifacts produced by a LangGraph control-plane MVP. The operator claims no personal authorship credit for the writing or results beyond releasing the artifact. Readers should treat this as an unreviewed AI-generated research artifact. No human reviewer has endorsed its conclusions.

---

## Abstract

We investigate whether a blind, multi-role paper-club swarm can reproducibly transform public full-paper PDFs into evidence-backed review artifacts without requiring private services or human intervention. We implement a dependency-light local harness (`blind_paper_swarm.py`) that downloads PDFs, extracts text, blinds front matter, and runs five deterministic independent review roles: claim mapping, methods reproducibility assessment, evidence auditing, skeptical limitation flagging, and blindness verification. We validate the prototype on two well-known public papers (Vaswani et al., 2017; Devlin et al., 2019) and a synthetic smoke-test input. The system produces structured review JSON artifacts with aggregate reviewability scores of 0.647 and 0.873 for the two papers respectively, completing in 0.22 seconds wall-clock time with 23.7 MB peak RSS on cached inputs. However, 14 of 27 detected claims in the first paper and 12 of 40 in the second were flagged as unsupported by nearby evidence, and PDF layout noise—particularly for two-column formats—degrades sentence and section detection. We conclude the prototype is viable as a local triage and review-assistance tool, but it does not establish final scientific validation, which requires domain-expert review, stronger PDF layout recovery, and external replication evidence.

## Introduction

Automated paper review assistance has attracted growing interest as publication volumes increase. A key challenge is producing structured, evidence-grounded review artifacts from raw manuscripts without relying on proprietary services or human labor. A secondary concern is blinding: ensuring that reviewer roles are not influenced by author identity or institutional affiliation embedded in the manuscript.

We pose the following research question: *Can a blind, multi-role paper-club swarm turn full paper PDFs into concrete, evidence-backed review artifacts without requiring private services or human intervention?*

By "blind" we mean that front matter is stripped and obvious identifiers are masked before review roles process the text. By "multi-role" we mean that distinct analytical perspectives (claim detection, reproducibility assessment, evidence auditing, skeptical review, and blindness verification) operate independently on the same blinded input. By "swarm" we mean a local, deterministic orchestration of these roles without a central LLM call or cloud dependency.

This work is explicitly scoped as a prototype validation. We do not claim that the system replaces expert peer review, adjudicates novelty, or verifies empirical correctness. Rather, we ask whether such a pipeline can produce useful structured artifacts reproducibly and within modest resource bounds.

## Method

### System Architecture

The system is implemented as a single Python script (`scripts/blind_paper_swarm.py`, 14,592 bytes) with no external ML dependencies. The pipeline consists of five stages:

1. **PDF Acquisition.** Public PDFs are downloaded via `urllib` from arXiv URLs. No authentication or private service access is required.

2. **Text Extraction.** The system `pdftotext` binary is invoked to convert PDF to plain text. Raw text is preserved alongside blinded text for auditability.

3. **Front-Matter Blinding.** The first section of extracted text (typically title, authors, affiliations) is removed. Obvious identifier patterns (email addresses, explicit author-name tokens) are masked. The blinding step is heuristic, not guaranteed to be complete.

4. **Independent Review Roles.** Five deterministic roles process the blinded text in parallel:
   - **claim_mapper:** Detects claim-like sentences (assertions of fact, performance, or novelty) and maps each to nearby evidence sentences within a fixed window.
   - **methods_reproducibility:** Scans for method descriptions, experiment configurations, code/dataset availability signals, and hyperparameter disclosures.
   - **evidence_auditor:** Identifies tables, figures, metrics, and statistical-test signals in the text.
   - **skeptic:** Flags limitations, risk statements, and hedging language.
   - **blindness_check:** Reports residual leakage indicators (author names, institutions, grant numbers) that survived the blinding step.

5. **Aggregation.** Per-role scores are combined into an `overall_reviewability_score` (0–1 scale) and a categorical verdict. The aggregation weights section structure, claim-evidence proximity, reproducibility signals, and limitation disclosure.

### Validation Protocol

We conducted three validation runs:

- **Smoke test.** A synthetic paper-like text was embedded directly in the script to verify pipeline correctness without network access. Output: `artifacts/results/smoke_synthetic.review.json`.

- **Full-paper run.** Two public arXiv papers were processed:
  - *Attention Is All You Need* (arXiv:1706.03762, 2,215,244 bytes PDF)
  - *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding* (arXiv:1810.04805, 775,166 bytes PDF)

- **Calibrated resource run.** The full-paper run was repeated under `/usr/bin/time -v` telemetry with memory snapshots before and after execution.

All runs were executed on a single machine with 0 KB swap (per project constraint), ~121 GB available memory, and cached PDFs.

## Results

### Smoke Test

The smoke test passed. The synthetic input yielded 3 detected claims, 4 evidence sentences, and a verdict of `reviewable_with_caveats`. This confirms basic pipeline integrity but does not validate analytical quality on real manuscripts.

### Full-Paper Results

| Paper | Characters | Sentences | Sections Found | Claims | Unsupported Claims | Evidence Sentences | Limitation Sentences |
|---|---:|---:|---|---:|---:|---:|---:|
| Attention Is All You Need | 60,123 | 264 | 7 | 27 | 14 | 31 | 7 |
| BERT | 93,599 | 344 | 11 | 40 | 12 | 73 | 4 |

**Aggregate Scores:**

| Paper | Section | Claim Support | Evidence Density | Reproducibility | Limitation Disclosure | Overall |
|---|---:|---:|---:|---:|---:|---:|
| Attention Is All You Need | 0.714 | 0.494 | 0.652 | 0.500 | 0.875 | 0.647 |
| BERT | 1.000 | 0.867 | 1.000 | 1.000 | 0.500 | 0.873 |

The Attention paper received a verdict of `reviewable_but_many_claims_need_manual_check`, driven primarily by its low claim-support score (0.494): 14 of 27 detected claims lacked nearby evidence sentences within the heuristic window. The BERT paper received `reviewable_with_caveats`, with a higher claim-support score (0.867) but a lower limitation-disclosure score (0.500), reflecting only 4 limitation sentences detected in the extracted text.

Analysis times were 0.018 seconds and 0.027 seconds for the two papers respectively (text analysis only, excluding download and extraction).

### Calibrated Resource Run

| Metric | Value |
|---|---|
| Wall-clock time | 0.22 s |
| Max RSS | 23,692 KB |
| MemAvailable (start) | 121,643,920 KB |
| MemAvailable (end) | 121,652,972 KB |
| SwapTotal | 0 KB |
| Exit status | 0 |

Memory delta was negligible (+8,952 KB available after run), and peak RSS of ~23 MB confirms the system operates well within the project's resource constraints. These figures apply only to the cached-PDF, deterministic-heuristic configuration tested; they do not characterize performance with LLM-based roles or large batch processing.

### Notion Page Access

The project's Notion page returned HTTP 200 with a generic app shell, but the downloaded HTML contained neither the page title nor substantive content. No project-specific acceptance criteria could therefore be retrieved or validated from this source.

## Limitations

1. **Deterministic heuristics cannot adjudicate truth or novelty.** The claim_mapper role detects claim-like sentences and maps nearby evidence, but it cannot verify whether a claim is factually correct, novel, or supported by the evidence it cites. The "unsupported claim" flag means only that no evidence sentence was found within the heuristic proximity window—not that the claim is false.

2. **PDF extraction noise.** The `pdftotext` extraction produces layout artifacts, especially for two-column papers. The BERT paper (two-column) yielded 93,599 characters of raw text with residual column-interleaving noise, even though section headers and evidence signals were largely recovered. Section and sentence boundary detection is degraded by this noise.

3. **Blinding is incomplete.** Front-matter removal and identifier masking are heuristic. Author names, institutions, and grant numbers may persist in the body text, acknowledgments, or references. The blindness_check role reports likely remaining markers but does not guarantee perfect de-identification.

4. **Small validation set.** Only two real papers were tested. Generalization to other domains, formats, or languages is not established.

5. **No gold-label comparison.** Without a labeled dataset of known unsupported, withdrawn, or replicated claims, precision and recall of the claim-evidence mapping cannot be quantified. The scores reported are internal heuristic aggregates, not validated against expert judgments.

6. **Notion content inaccessible.** The project Notion page did not expose substantive content via public HTML, so no external acceptance criteria could be verified.

7. **No LLM or human baseline.** The current prototype uses only deterministic heuristics. It is unknown how its outputs compare to LLM-based or human review on the same inputs.

## Reproducibility Checklist

- [x] **Source code available.** `scripts/blind_paper_swarm.py` (14,592 bytes, SHA256: `0bcd54deb74e6146f869ffb633a1352e4d1c0ba72baf87bdd2fc6757faa3985b`).
- [x] **Input data specified.** Public arXiv URLs: `https://arxiv.org/pdf/1706.03762`, `https://arxiv.org/pdf/1810.04805`.
- [x] **Output artifacts preserved.** Review JSONs, raw/blinded text, telemetry logs, and run summary are recorded with SHA256 hashes in the project decision artifact.
- [x] **Execution environment described.** System `pdftotext` required; Python 3 with no ML dependencies; 0 KB swap; ~121 GB RAM available.
- [x] **Randomness controlled.** All roles are deterministic; no random seeds required.
- [x] **Resource bounds measured.** Calibrated run with `/usr/bin/time -v` and memory telemetry snapshots.
- [ ] **Gold-label validation.** Not performed; no labeled claim/evidence dataset available.
- [ ] **External replication.** Not performed beyond the single-machine calibrated run.
- [ ] **Human expert comparison.** Not performed.

## Conclusion

We have demonstrated that a local, deterministic, multi-role paper-club swarm can reproducibly transform public full-paper PDFs into structured review artifacts—claim maps, evidence proximity scores, reproducibility signals, limitation flags, and aggregate reviewability scores—without private services or human intervention. The prototype completed processing of two full papers in 0.22 seconds wall-clock time with 23.7 MB peak RSS.

However, the results reveal significant caveats. Over half of detected claims in the Attention paper (14/27) and nearly a third in the BERT paper (12/40) were flagged as lacking nearby evidence, but this reflects heuristic proximity matching rather than verified unsupported status. PDF extraction noise, incomplete blinding, the absence of gold-label validation, and the small test set all constrain the strength of the viability claim.

The system is viable as a triage and review-assistance tool for structuring initial paper assessments. It is not viable as a substitute for expert peer review, empirical verification, or novelty adjudication. Closing the gap would require: (1) gold-label datasets with known claim/evidence mappings to measure precision and recall; (2) stronger PDF layout recovery (e.g., GROBID or S2ORC) before scaling; and (3) controlled comparison of deterministic heuristics against LLM-based and human reviewers on the same blinded inputs.

---

## Referenced Artifacts

| Artifact | Path | SHA256 |
|---|---|---|
| Swarm script | `scripts/blind_paper_swarm.py` | `0bcd54deb74e6146f869ffb633a1352e4d1c0ba72baf87bdd2fc6757faa3985b` |
| Attention PDF | `artifacts/data/attention_is_all_you_need.pdf` | `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697` |
| Attention raw text | `artifacts/data/attention_is_all_you_need.raw.txt` | `b217207e00a758cbb7f5d0cc18ad8ae4a7c52d74ca03d9273a143cdbfc9d4858` |
| Attention blinded text | `artifacts/data/attention_is_all_you_need.blinded.txt` | `b858f62b1e7ccef8413c6dc468a299d2baf21c646d20073f0c5926165601cf80` |
| Attention review | `artifacts/results/attention_is_all_you_need.review.json` | `88b418c85a4cff1c007670ae49dc194550be47a9f8925925ce5ea8803161aecd` |
| BERT PDF | `artifacts/data/bert.pdf` | `5692a5514787a8c6727b4ff3b726a3385798bc68e12138d1d4af83947e2acf6e` |
| BERT raw text | `artifacts/data/bert.raw.txt` | `298c3369eb308aa2dc96414802b5dc2e994c7f58a3b0c4067cb61620cf4d5f1c` |
| BERT blinded text | `artifacts/data/bert.blinded.txt` | `257bbeb201f0327e8f4f6be6d8af7e0d126f20bc59b7b025e72f875b855d5fa0` |
| BERT review | `artifacts/results/bert.review.json` | `0f7586b4949009af82aa1ebc8ca5305c30e70a4cc6805f263e1051bcebc7dd3c` |
| Smoke test review | `artifacts/results/smoke_synthetic.review.json` | `17eccc94abe6cf9112dc9ed64f721faa0bebc96c2fdaca9b939ece59099e4538` |
| Run summary | `artifacts/results/run_summary.json` | `9cbc82cb4b25a3d689b080ec30ae77ec04fe67d89ed27bbb52acaad5ebaebbf7` |
| Calibrated run log | `artifacts/logs/calibrated_full_run.log` | `a2552e7e5a6dfc3848b40ead09911b3b06b1ebec6e9b2939ea8b63dcb86f3b22` |
| Telemetry start | `artifacts/logs/calibrated_telemetry_start.log` | `b2b2968ec19a388c66d004e29a98ad4201ed287cdb606ef1fae7ab64b6f4660b` |
| Telemetry end | `artifacts/logs/calibrated_telemetry_end.log` | `bbc84a270e057d069a11ed50738702bdb12af67144becb7d09f022ef1306fc87` |
| Notion HEAD log | `artifacts/logs/notion_head.log` | `01a0b49b4419816247afd7443a3363a0e9cc5299656c7bbf97099f49c0666009` |
| Notion page HTML | `artifacts/logs/notion_page.html` | `fc21ade3d39d2cbb342dc0a1a4685f43f2e7e7bd3cf0d49caae7b6ff8c5fd247` |
| Project decision | `.omx/project_decision.json` | (in project directory) |
| Run notes | `run_notes.md` | `19196c7800a794c914b90af87cd355579cfb6e454cbf4236756dd26fabd2b1d5` |
| Claim ledger | `papers/.../claim_ledger.json` | (empty claims list) |
| Evidence bundle | `papers/.../evidence_bundle.json` | (source metadata only) |
| Paper manifest | `papers/.../paper_manifest.json` | (generation metadata) |
