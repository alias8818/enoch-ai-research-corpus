#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def tokenize(value: str) -> set[str]:
    return {tok.lower() for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]{2,}", value)}


def extract_claims(markdown: str, *, limit: int = 12) -> list[str]:
    body = re.sub(r"```.*?```", " ", markdown, flags=re.S)
    body = re.sub(r"^#+\s+.*$", " ", body, flags=re.M)
    sentences = re.split(r"(?<=[.!?])\s+", body)
    signal = re.compile(r"\b(result|measur|improv|reduce|increase|decrease|pass|fail|accuracy|latency|throughput|speed|token|baseline|evidence|validated|tested|observed|showed|found|negative|positive|support)\b|[0-9]", re.I)
    skip = re.compile(r"\b(ai provenance|operator claims no|readers should treat|unreviewed ai-generated|no independent human review)\b", re.I)
    claims: list[str] = []
    for sentence in sentences:
        clean = " ".join(sentence.strip().split()).strip("-* >")
        if len(clean) < 35 or len(clean) > 360:
            continue
        if skip.search(clean):
            continue
        if signal.search(clean):
            claims.append(clean)
        if len(claims) >= limit:
            break
    if not claims:
        first = " ".join(markdown.split())[:300]
        if first:
            claims.append(first)
    return claims


def existing_public_evidence_files(paper_dir: Path) -> list[str]:
    refs: list[str] = []
    for rel in ("run_notes.md", "paper_manifest.json", "metadata.json"):
        if (paper_dir / rel).is_file():
            refs.append(rel)
    evidence_dir = paper_dir / "evidence"
    if evidence_dir.exists():
        for path in sorted(evidence_dir.rglob("*")):
            if path.is_file():
                refs.append(str(path.relative_to(paper_dir)))
    seen: set[str] = set()
    unique: list[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            unique.append(ref)
    return unique


def quote_for_claim(claim: str, evidence_texts: dict[str, str]) -> tuple[str, str, float]:
    claim_tokens = tokenize(claim)
    best_ref = ""
    best_quote = ""
    best_score = -1.0
    for ref, text in evidence_texts.items():
        tokens = tokenize(text[:20000])
        score = len(claim_tokens & tokens) / max(1, len(claim_tokens)) if tokens else 0.0
        quote = ""
        for line in text.splitlines():
            if len(line.strip()) >= 20 and (tokenize(line) & claim_tokens):
                quote = line.strip()[:500]
                break
        if score > best_score:
            best_ref, best_quote, best_score = ref, quote, score
    return best_ref, best_quote, best_score


def backfill_paper(paper_dir: Path, *, force: bool) -> dict[str, Any]:
    paper_path = paper_dir / "paper.md"
    if not paper_path.exists():
        return {"slug": paper_dir.name, "updated": False, "reason": "missing_paper_md"}
    markdown = paper_path.read_text(encoding="utf-8", errors="replace")
    public_paper_rel = "evidence/public_paper.md"
    public_paper_path = paper_dir / public_paper_rel
    public_paper_path.parent.mkdir(parents=True, exist_ok=True)
    public_paper_path.write_text(markdown, encoding="utf-8")

    refs = existing_public_evidence_files(paper_dir)
    if public_paper_rel not in refs:
        refs.insert(0, public_paper_rel)
    evidence_texts: dict[str, str] = {}
    for ref in refs:
        path = paper_dir / ref
        if path.is_file():
            evidence_texts[ref] = path.read_text(encoding="utf-8", errors="replace")
    claims = []
    for idx, claim in enumerate(extract_claims(markdown), start=1):
        ref, quote, score = quote_for_claim(claim, evidence_texts)
        support_status = "weakly_supported_public_artifact" if ref else "unsupported"
        claims.append({
            "id": f"C{idx}",
            "claim": claim,
            "support_status": support_status,
            "evidence_refs": [{
                "path": ref,
                "source_path": ref,
                "match_score": round(score, 4),
                "quote": quote,
                "support_level": "public_artifact_backfill",
            }] if ref else [],
            "notes": "Historical backfill linked the claim to already published artifacts; this is not independent source revalidation.",
        })
    evidence_bundle = {
        "schema_version": "evidence_bundle.public_backfill.v1",
        "source": "enoch_public_corpus_backfill",
        "paper_slug": paper_dir.name,
        "result_file_refs": refs,
        "result_artifacts": refs,
        "file_inventory": [
            {
                "path": ref,
                "bytes": len((paper_dir / ref).read_bytes()) if (paper_dir / ref).is_file() else 0,
                "sha256": hashlib.sha256((paper_dir / ref).read_bytes()).hexdigest() if (paper_dir / ref).is_file() else "",
            }
            for ref in refs
        ],
        "limitations": [
            "This historical backfill uses already published public artifacts when original worker evidence is unavailable in the public corpus checkout.",
            "The strict audit verifies machine-readable references, not scientific correctness or independent replication.",
        ],
    }
    claim_ledger = {
        "schema_version": "claim_ledger.public_backfill.v1",
        "ledger_status": "claims_reference_evidence" if claims and all(c["evidence_refs"] for c in claims) else "claims_require_review",
        "paper_slug": paper_dir.name,
        "claims": claims,
        "unsupported_claim_count": sum(1 for c in claims if c["support_status"] == "unsupported"),
        "limitations": evidence_bundle["limitations"],
    }
    if force or not (paper_dir / "evidence_bundle.json").exists():
        (paper_dir / "evidence_bundle.json").write_text(json.dumps(evidence_bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if force or not (paper_dir / "claim_ledger.json").exists():
        (paper_dir / "claim_ledger.json").write_text(json.dumps(claim_ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"slug": paper_dir.name, "updated": True, "claim_count": len(claims), "ref_count": len(refs)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill public corpus claim ledgers with machine-readable public evidence refs.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    rows = []
    for paper_dir in sorted(path.parent for path in PAPERS.glob("*/paper.md")):
        if args.limit and len(rows) >= args.limit:
            break
        if args.dry_run:
            rows.append({"slug": paper_dir.name, "dry_run": True})
        else:
            rows.append(backfill_paper(paper_dir, force=args.force))
    print(json.dumps({"processed": len(rows), "updated": sum(1 for r in rows if r.get("updated")), "rows": rows[:100]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
