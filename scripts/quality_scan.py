#!/usr/bin/env python3
from __future__ import annotations

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
report = {"count": len(rows), "passed": sum(1 for r in rows if r["passes"]), "failed": sum(1 for r in rows if not r["passes"]), "rows": rows}
(QUALITY / "quality_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
lines = ["# Corpus quality report", "", f"Passed: {report['passed']} / {report['count']}", "", "| Paper | Passes | Issues |", "|---|---:|---|"]
for row in rows:
    lines.append(f"| `{row['slug']}` | {row['passes']} | {json.dumps(row['issues'], sort_keys=True)} |")
(QUALITY / "quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("count", "passed", "failed")}, indent=2))
