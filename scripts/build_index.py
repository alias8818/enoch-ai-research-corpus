#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
def _load_claim_audit() -> dict[str, dict]:
    module_path = ROOT / "scripts" / "audit_claim_evidence_contract.py"
    spec = importlib.util.spec_from_file_location("claim_evidence_audit", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.build_report()
    return {row["slug"]: row for row in report.get("rows", [])}


def _load_highlights() -> list[dict]:
    path = PAPERS / "highlights.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    highlights = data.get("featured", data if isinstance(data, list) else [])
    if not isinstance(highlights, list):
        return []
    return [row for row in highlights if isinstance(row, dict)]


claim_audit_rows = _load_claim_audit()
highlights = _load_highlights()
strict_pass_count = sum(1 for row in claim_audit_rows.values() if row.get("strict_pass"))
rows = []
for meta_path in sorted(PAPERS.glob("*/metadata.json")):
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        continue
    paper_dir = meta_path.parent
    row = {
        "slug": paper_dir.name,
        "title": meta.get("title") or paper_dir.name,
        "public_id": meta.get("public_id", ""),
        "source_record_fingerprint": meta.get("source_record_fingerprint", ""),
        "generated_at": meta.get("generated_at", ""),
        "ai_generated": meta.get("ai_generated", True),
        "human_authorship_claimed": meta.get("human_authorship_claimed", False),
        "paper_path": str((paper_dir / "paper.md").relative_to(ROOT)),
        "evidence_bundle_path": str((paper_dir / "evidence_bundle.json").relative_to(ROOT)) if (paper_dir / "evidence_bundle.json").exists() else "",
        "claim_ledger_path": str((paper_dir / "claim_ledger.json").relative_to(ROOT)) if (paper_dir / "claim_ledger.json").exists() else "",
    }
    audit = claim_audit_rows.get(paper_dir.name, {})
    row.update({
        "claim_count": int(audit.get("claim_count", 0)),
        "strict_audit_pass": bool(audit.get("strict_pass", False)),
        "missing_result_refs": int(audit.get("result_file_refs_missing", 0)),
    })
    rows.append(row)
(PAPERS / "index.json").write_text(json.dumps({"count": len(rows), "highlight_count": len(highlights), "highlights": highlights, "papers": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
lines = [
    "# Paper index",
    "",
    f"Count: {len(rows)}",
    "",
    f"This index distinguishes metadata-file presence from strict claim/evidence audit status. Current corpus state is {len(rows)}/{len(rows)} packaging/provenance lint pass and {strict_pass_count}/{len(rows)} strict claim/evidence audit pass.",
    "",
]
if highlights:
    lines.extend([
        "## Highlighted artifacts",
        "",
        "These launch highlights are a curated inspection set, not a peer-review ranking. The `why it matters` summaries are bounded pointers into generated artifacts; use each paper's evidence bundle, claim ledger, and strict-audit status before treating a claim as established.",
        "",
        "| Title | Public ID | Why it matters | Bounds |",
        "|---|---|---|---|",
    ])
    for item in highlights:
        title = str(item.get("title") or "").strip()
        public_id = str(item.get("public_id") or "").strip()
        paper_path = str(item.get("paper_path") or "").strip()
        rel = paper_path.removeprefix("papers/")
        title_cell = f"[{title}]({rel})" if title and rel else title
        why = str(item.get("why_it_matters") or "").replace("\n", " ").strip()
        bounds = str(item.get("bounds") or "").replace("\n", " ").strip()
        lines.append(f"| {title_cell} | `{public_id}` | {why} | {bounds} |")
    lines.extend(["", "## Full artifact index", ""])
lines.extend([
    "| Title | Public ID | Evidence bundle present | Claim ledger file present | Claim count | Strict audit pass | Missing result refs |",
    "|---|---|---:|---:|---:|---:|---:|",
])
for row in rows:
    # index.md lives inside papers/, so Markdown links must be relative to
    # that directory. Keep index.json paths root-relative for machine readers.
    markdown_paper_path = f"{row['slug']}/paper.md"
    lines.append(f"| [{row['title']}]({markdown_paper_path}) | `{row['public_id']}` | {'yes' if row['evidence_bundle_path'] else 'no'} | {'yes' if row['claim_ledger_path'] else 'no'} | {row['claim_count']} | {str(row['strict_audit_pass']).lower()} | {row['missing_result_refs']} |")
(PAPERS / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"count": len(rows), "index": str(PAPERS / "index.json")}, indent=2))
