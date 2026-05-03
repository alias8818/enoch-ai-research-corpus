#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
QUALITY = ROOT / "quality"
QUALITY.mkdir(exist_ok=True)
patterns = {
    "todo": re.compile(r"TODO|FIXME|citation needed|\[TODO|\[citation", re.I),
    "human_review_required": re.compile(r"requires human review|human review before", re.I),
    "human_authorship_claim": re.compile(r"human authored|human author(?!ship_claimed: false)", re.I),
}
peer_review_rx = re.compile(r"peer[- ]reviewed", re.I)
peer_review_negation_rx = re.compile(r"\b(not|no|never|unreviewed)\b.{0,80}peer[- ]reviewed|peer[- ]reviewed.{0,80}\b(not|no|never)\b", re.I)
rows = []
GATE_NAME = "packaging_provenance_gate"
GATE_VERSION = "1.0"
VALIDATED = [
    "ai_provenance_notice_present",
    "no_placeholder_citation_patterns",
    "no_unsupported_human_authorship_claim",
    "no_unsupported_peer_review_claim",
    "evidence_bundle_present",
    "claim_ledger_present",
]
NOT_VALIDATED = [
    "peer_review",
    "scientific_correctness",
    "external_replication",
    "statistical_power",
    "semantic_output_quality",
    "citation_accuracy",
    "strict_claim_evidence_audit",
]


def _run_claim_evidence_audit() -> dict:
    module_path = ROOT / "scripts" / "audit_claim_evidence_contract.py"
    spec = importlib.util.spec_from_file_location("claim_evidence_audit", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    audit = module.build_report()
    (QUALITY / "claim_evidence_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    module.write_markdown(audit, QUALITY / "claim_evidence_audit.md")
    return audit
for paper in sorted(PAPERS.glob("*/paper.md")):
    text = paper.read_text(encoding="utf-8", errors="replace")
    issues = {name: len(rx.findall(text)) for name, rx in patterns.items()}
    peer_review_claims = 0
    for match in peer_review_rx.finditer(text):
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)
        if not peer_review_negation_rx.search(text[start:end]):
            peer_review_claims += 1
    if peer_review_claims:
        issues["peer_review_claim"] = peer_review_claims
    issues = {k: v for k, v in issues.items() if v}
    has_provenance = bool(re.search(r"AI Provenance|AI-generated|autonomous AI research", text, re.I))
    row = {
        "slug": paper.parent.name,
        "paper_path": str(paper.relative_to(ROOT)),
        "bytes": paper.stat().st_size,
        "words": len(re.findall(r"\w+", text)),
        "has_provenance": has_provenance,
        "has_evidence_bundle": (paper.parent / "evidence_bundle.json").exists(),
        "has_claim_ledger": (paper.parent / "claim_ledger.json").exists(),
        "issues": issues,
        "passes": has_provenance and not issues and (paper.parent / "evidence_bundle.json").exists() and (paper.parent / "claim_ledger.json").exists(),
    }
    rows.append(row)
claim_evidence_audit = _run_claim_evidence_audit()
report = {
    "gate_name": GATE_NAME,
    "gate_version": GATE_VERSION,
    "gate_scope": "artifact packaging, provenance, placeholder, and overclaim linting",
    "validated": VALIDATED,
    "not_validated": NOT_VALIDATED,
    "count": len(rows),
    "passed": sum(1 for r in rows if r["passes"]),
    "failed": sum(1 for r in rows if not r["passes"]),
    "claim_evidence_audit": {
        "gate_name": claim_evidence_audit["gate_name"],
        "status": claim_evidence_audit["status"],
        "strict_claim_evidence_pass_count": claim_evidence_audit["strict_claim_evidence_pass_count"],
        "count": claim_evidence_audit["count"],
        "claim_ledgers_empty": claim_evidence_audit["claim_ledgers_empty"],
        "result_file_refs": claim_evidence_audit["result_file_refs"],
        "result_file_refs_missing": claim_evidence_audit["result_file_refs_missing"],
        "gap_summary": claim_evidence_audit["gap_summary"],
    },
    "rows": rows,
}
(QUALITY / "quality_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
(QUALITY / "packaging_provenance_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
lines = [
    "# Corpus packaging/provenance report",
    "",
    f"Packaging/provenance passed: {report['passed']} / {report['count']}",
    "",
    "This gate checks artifact packaging, provenance language, placeholder/overclaim patterns, and presence of evidence/claim metadata files. It does not validate scientific correctness, peer review, independent replication, statistical power, semantic output quality, citation accuracy, or strict claim/evidence auditability.",
    "",
    "## Validated",
    "",
]
lines.extend(f"- `{item}`" for item in VALIDATED)
lines.extend(["", "## Not validated", ""])
lines.extend(f"- `{item}`" for item in NOT_VALIDATED)
lines.extend([
    "",
    "## Strict claim/evidence audit",
    "",
    f"Strict claim/evidence passed: {claim_evidence_audit['strict_claim_evidence_pass_count']} / {claim_evidence_audit['count']}",
    f"Status: `{claim_evidence_audit['status']}`",
    f"Gap summary: {claim_evidence_audit['gap_summary']}",
    "",
    "| Paper | Passes | Issues |",
    "|---|---:|---|",
])
for row in rows:
    lines.append(f"| `{row['slug']}` | {row['passes']} | {json.dumps(row['issues'], sort_keys=True)} |")
(QUALITY / "quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(QUALITY / "packaging_provenance_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("count", "passed", "failed")}, indent=2))
