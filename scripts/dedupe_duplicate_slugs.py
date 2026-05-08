#!/usr/bin/env python3
"""Collapse duplicate public paper slug directories.

Canonical rule: for a cluster where the only difference is a trailing
10-character hex suffix, keep the unsuffixed slug directory. If that canonical
ledger is empty and a suffixed sibling has claims, restore the richest sibling
claim ledger to the canonical directory before deleting the suffixed siblings.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEX_SUFFIX = re.compile(r"^(.*)-[0-9a-f]{10}$")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def claim_count(slug_dir: Path) -> int:
    ledger = slug_dir / "claim_ledger.json"
    if not ledger.exists():
        return 0
    data = load_json(ledger)
    claims = data.get("claims") or []
    return len(claims) if isinstance(claims, list) else 0


def generated_at(slug_dir: Path) -> str:
    try:
        return str(load_json(slug_dir / "metadata.json").get("generated_at") or "")
    except Exception:
        return ""


def public_id(slug_dir: Path) -> str:
    try:
        return str(load_json(slug_dir / "metadata.json").get("public_id") or "")
    except Exception:
        return ""


def choose_source(canonical: Path, siblings: list[Path]) -> Path | None:
    if claim_count(canonical) > 0:
        return None
    candidates = [p for p in siblings if p != canonical and claim_count(p) > 0]
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: (claim_count(p), generated_at(p), p.name), reverse=True)[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--papers", type=Path, default=Path("papers"))
    ap.add_argument("--report", type=Path, default=Path("quality/duplicate_slug_cleanup_report.json"))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    papers = args.papers
    clusters: dict[str, list[Path]] = {}
    for child in papers.iterdir():
        if not child.is_dir():
            continue
        match = HEX_SUFFIX.match(child.name)
        base = match.group(1) if match else child.name
        clusters.setdefault(base, []).append(child)

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "canonical_rule": "keep unsuffixed slug; restore richest claimed sibling ledger only when canonical ledger is empty; remove suffixed siblings",
        "applied": bool(args.apply),
        "before": {
            "slug_directory_count": sum(1 for p in papers.iterdir() if p.is_dir()),
            "canonical_base_count": len(clusters),
            "duplicate_cluster_count": sum(1 for v in clusters.values() if len(v) > 1),
            "duplicate_directory_count": sum(len(v) - 1 for v in clusters.values() if len(v) > 1),
        },
        "clusters": [],
    }

    for base, members in sorted(clusters.items()):
        if len(members) < 2:
            continue
        canonical = papers / base
        if canonical not in members:
            raise SystemExit(f"No unsuffixed canonical directory for duplicate cluster {base!r}")
        members = sorted(members, key=lambda p: (p.name != base, p.name))
        source = choose_source(canonical, members)
        removed = [p for p in members if p != canonical]
        entry = {
            "base_slug": base,
            "canonical_slug": canonical.name,
            "canonical_claims_before": claim_count(canonical),
            "ledger_source_slug": source.name if source else None,
            "ledger_source_claims": claim_count(source) if source else 0,
            "removed_slugs": [p.name for p in removed],
            "members": [
                {
                    "slug": p.name,
                    "claims": claim_count(p),
                    "generated_at": generated_at(p),
                    "public_id": public_id(p),
                }
                for p in members
            ],
        }
        report["clusters"].append(entry)
        if args.apply:
            if source:
                shutil.copy2(source / "claim_ledger.json", canonical / "claim_ledger.json")
            for p in removed:
                shutil.rmtree(p)

    if args.apply:
        after_slugs = [p for p in papers.iterdir() if p.is_dir()]
        after_clusters: dict[str, list[Path]] = {}
        for child in after_slugs:
            match = HEX_SUFFIX.match(child.name)
            base = match.group(1) if match else child.name
            after_clusters.setdefault(base, []).append(child)
        report["after"] = {
            "slug_directory_count": len(after_slugs),
            "canonical_base_count": len(after_clusters),
            "duplicate_cluster_count": sum(1 for v in after_clusters.values() if len(v) > 1),
            "duplicate_directory_count": sum(len(v) - 1 for v in after_clusters.values() if len(v) > 1),
            "canonical_ledgers_restored": sum(1 for e in report["clusters"] if e["ledger_source_slug"]),
        }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps({k: report[k] for k in ("applied", "before")}, indent=2, sort_keys=True))
    if args.apply:
        print(json.dumps({"after": report["after"]}, indent=2, sort_keys=True))
    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
