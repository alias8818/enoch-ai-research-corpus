#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import hashlib
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
ARTIFACT_FIELDS = [
    "draft_markdown_path",
    "evidence_bundle_path",
    "claim_ledger_path",
    "manifest_path",
]


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return (slug or fallback)[:120]


def sanitize_public_content(content: str) -> str:
    content = re.sub(r"idea-[0-9a-f]{32}(?:-[0-9]{14})?", "source-record-redacted", content)
    content = content.replace("/var/lib/enoch-control-plane/projects", "<control-plane-projects>")
    content = content.replace("/var/lib/enoch-control-plane", "<control-plane-state>")
    return content


def request_json(base_url: str, token: str, path: str) -> dict[str, Any]:
    req = urllib.request.Request(base_url.rstrip("/") + path, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 - operator-provided control URL
        return json.loads(resp.read())


def main() -> int:
    parser = argparse.ArgumentParser(description="Import generated paper artifacts from the Enoch control plane API.")
    parser.add_argument("--control-url", default=os.environ.get("ENOCH_CONTROL_URL", "http://127.0.0.1:8787"))
    parser.add_argument("--token", default=os.environ.get("ENOCH_CONTROL_TOKEN", ""))
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--limit", type=int, default=0, help="Optional maximum papers to import")
    parser.add_argument("--paper-status", default="publication_draft")
    args = parser.parse_args()
    if not args.token:
        print("Set --token or ENOCH_CONTROL_TOKEN", file=sys.stderr)
        return 2
    PAPERS.mkdir(parents=True, exist_ok=True)
    imported = 0
    page = 1
    while True:
        qs = urllib.parse.urlencode({"page": page, "page_size": args.page_size, "paper_status": args.paper_status, "include_rank_reasons": "false"})
        listing = request_json(args.control_url, args.token, f"/control/api/paper-reviews?{qs}")
        rows = listing.get("rows") or []
        if not rows:
            break
        for row in rows:
            paper_id = str(row.get("paper_id") or "")
            project_name = str(row.get("project_name") or paper_id)
            project_id = str(row.get("project_id") or "")
            base_slug = slugify(project_name, project_id or paper_id[:16])
            slug = base_slug
            paper_dir = PAPERS / slug
            if (paper_dir / "metadata.json").exists():
                try:
                    existing = json.loads((paper_dir / "metadata.json").read_text(encoding="utf-8"))
                except Exception:
                    existing = {}
                if existing.get("paper_id") != paper_id:
                    suffix = hashlib.sha1(paper_id.encode("utf-8")).hexdigest()[:10]
                    slug = f"{base_slug[:109]}-{suffix}"
                    paper_dir = PAPERS / slug
            paper_dir.mkdir(parents=True, exist_ok=True)
            public_id = f"enoch-paper-{imported + 1:04d}"
            metadata = {
                "public_id": public_id,
                "source_record_fingerprint": hashlib.sha256(paper_id.encode("utf-8")).hexdigest()[:16],
                "title": project_name,
                "generated_at": row.get("generated_at") or row.get("updated_at") or "",
                "ai_generated": True,
                "generated_by": "Enoch Agentic Research Pipeline",
                "released_by_role": "system operator and corpus maintainer",
                "human_authorship_claimed": False,
                "review_status": "AI-generated research artifact",
                "source_system": "Enoch control plane export",
            }
            (paper_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            for field in ARTIFACT_FIELDS:
                try:
                    artifact = request_json(args.control_url, args.token, f"/control/api/papers/{urllib.parse.quote(paper_id, safe='')}/artifact/{field}")
                except Exception as exc:  # keep partial imports inspectable
                    (paper_dir / f"{field}.missing.txt").write_text(f"missing {field}: {type(exc).__name__}: {exc}\n", encoding="utf-8")
                    continue
                content = sanitize_public_content(str(artifact.get("content") or ""))
                target_name = {
                    "draft_markdown_path": "paper.md",
                    "evidence_bundle_path": "evidence_bundle.json",
                    "claim_ledger_path": "claim_ledger.json",
                    "manifest_path": "paper_manifest.json",
                }[field]
                (paper_dir / target_name).write_text(content, encoding="utf-8")
            imported += 1
            if args.limit and imported >= args.limit:
                print(json.dumps({"imported": imported}, indent=2))
                return 0
        total = int((listing.get("page") or {}).get("total") or imported)
        if page * args.page_size >= total:
            break
        page += 1
    print(json.dumps({"imported": imported}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
