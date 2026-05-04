#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
QUALITY = ROOT / "quality"
STRICT_GATE_NAME = "strict_claim_evidence_audit"
STRICT_GATE_VERSION = "1.0"
FEATURED_SLUGS = {
    "vllm-attention-sink-retention-3b-continuous-serving-stress-campaign",
    "gb10-dense-router-retrofit-strict-audit-bundle",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def iter_paper_dirs() -> Iterable[Path]:
    return sorted(path.parent for path in PAPERS.glob("*/paper.md"))


def collect_result_file_refs(value: Any) -> list[str]:
    refs: list[str] = []

    def add(item: Any) -> None:
        if isinstance(item, str) and item.strip():
            refs.append(item.strip())
        elif isinstance(item, dict):
            for key in ("path", "file", "result_file", "result_path"):
                candidate = item.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    refs.append(candidate.strip())
                    break

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key in {"result_files", "result_file_refs", "result_artifacts"}:
                    if isinstance(child, list):
                        for item in child:
                            add(item)
                    else:
                        add(child)
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    # Keep order for human diffability while removing duplicates.
    seen: set[str] = set()
    unique: list[str] = []
    for ref in refs:
        normalized = ref.lstrip("./")
        if normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def ref_exists(paper_dir: Path, ref: str) -> bool:
    """Return true only for public, repository-relative evidence refs.

    Absolute local paths must never make the public strict audit pass: they can
    exist on a maintainer machine while remaining absent from the published repo.
    Represent private/absolute evidence with explicit unavailability metadata
    instead.
    """
    ref_path = Path(ref)
    if ref_path.is_absolute():
        return False
    normalized = Path(ref.lstrip("./"))
    candidates = [(paper_dir / normalized).resolve(), (ROOT / normalized).resolve()]
    for path in candidates:
        try:
            path.relative_to(ROOT)
        except ValueError:
            continue
        if path.exists() and path.is_file():
            return True
    return False


def is_declared_unavailable(value: Any, ref: str) -> bool:
    """Return true only for complete per-reference unavailability records.

    Absolute/private refs require reason, sha256, bytes, and public_surrogate so
    the public audit cannot pass because a private local file happened to exist.
    When metadata hashes the public surrogate rather than the unavailable
    original file, require an explicit sha256_scope and verify the surrogate
    file's current digest and byte count.
    """
    if not isinstance(value, dict):
        return False
    unavailable = value.get("unavailable_result_files") or value.get("redacted_result_files") or []
    if not isinstance(unavailable, list):
        return False
    for item in unavailable:
        if isinstance(item, str):
            continue
        if isinstance(item, dict):
            path = item.get("path") or item.get("file")
            reason = str(item.get("reason") or item.get("status") or "").lower()
            sha256 = item.get("sha256")
            byte_count = item.get("bytes")
            surrogate = item.get("public_surrogate")
            sha256_scope = item.get("sha256_scope")
            path_matches = isinstance(path, str) and path.lstrip("./") == ref.lstrip("./")
            has_base_metadata = (
                reason in {"not_public", "redacted", "private", "unavailable", "omitted"}
                and isinstance(sha256, str)
                and bool(re.fullmatch(r"[0-9a-fA-F]{64}", sha256))
                and isinstance(byte_count, int)
                and byte_count >= 0
                and isinstance(surrogate, str)
                and bool(surrogate.strip())
                and not Path(surrogate).is_absolute()
            )
            if not (path_matches and has_base_metadata):
                continue

            surrogate_path = (ROOT / surrogate.lstrip("./")).resolve()
            try:
                surrogate_path.relative_to(ROOT)
            except ValueError:
                continue
            if not surrogate_path.exists() or not surrogate_path.is_file():
                continue

            if sha256_scope == "public_surrogate":
                import hashlib

                data = surrogate_path.read_bytes()
                if hashlib.sha256(data).hexdigest().lower() != sha256.lower():
                    continue
                if len(data) != byte_count:
                    continue
            elif sha256_scope not in {None, "original_result_file"}:
                continue

            if path_matches:
                return True
    return False


def claim_has_evidence_refs(claim: dict[str, Any]) -> bool:
    for key in ("evidence_refs", "evidence", "supporting_evidence", "result_files", "source_refs"):
        value = claim.get(key)
        if isinstance(value, list) and value:
            return True
        if isinstance(value, str) and value.strip():
            return True
    return False


def audit_paper(paper_dir: Path) -> dict[str, Any]:
    slug = paper_dir.name
    ledger_path = paper_dir / "claim_ledger.json"
    evidence_path = paper_dir / "evidence_bundle.json"
    issues: list[str] = []
    claims: list[Any] = []
    ledger_status = "missing"
    evidence_refs: list[str] = []
    present_refs: list[str] = []
    missing_refs: list[str] = []
    declared_unavailable_refs: list[str] = []

    if ledger_path.exists():
        try:
            ledger = load_json(ledger_path)
            claims_value = ledger.get("claims") if isinstance(ledger, dict) else None
            claims = claims_value if isinstance(claims_value, list) else []
            if not isinstance(ledger, dict):
                issues.append("claim_ledger_not_object")
            elif not isinstance(claims_value, list):
                issues.append("claim_ledger_claims_not_list")
            elif not claims:
                issues.append("claim_ledger_empty_claims")
                ledger_status = "blocked_empty_claims"
            else:
                malformed = [idx for idx, claim in enumerate(claims) if not isinstance(claim, dict) or not claim_has_evidence_refs(claim)]
                if malformed:
                    issues.append("claims_missing_evidence_refs")
                    ledger_status = "blocked_claims_missing_evidence_refs"
                else:
                    ledger_status = "claims_reference_evidence"
        except Exception as exc:  # pragma: no cover - defensive report path
            issues.append(f"claim_ledger_invalid_json:{type(exc).__name__}")
    else:
        issues.append("claim_ledger_missing")

    evidence_data: Any = {}
    if evidence_path.exists():
        try:
            evidence_data = load_json(evidence_path)
            evidence_refs = collect_result_file_refs(evidence_data)
            for ref in evidence_refs:
                if ref_exists(paper_dir, ref):
                    present_refs.append(ref)
                elif is_declared_unavailable(evidence_data, ref):
                    declared_unavailable_refs.append(ref)
                else:
                    missing_refs.append(ref)
            if missing_refs:
                issues.append("evidence_result_files_missing_public_artifacts")
        except Exception as exc:  # pragma: no cover - defensive report path
            issues.append(f"evidence_bundle_invalid_json:{type(exc).__name__}")
    else:
        issues.append("evidence_bundle_missing")

    strict_pass = bool(claims) and ledger_status == "claims_reference_evidence" and not missing_refs
    if strict_pass:
        audit_status = "strict_pass"
    elif not claims:
        audit_status = "blocked_empty_claims"
    elif missing_refs:
        audit_status = "blocked_missing_result_files"
    else:
        audit_status = "blocked_schema_or_evidence_gap"

    return {
        "slug": slug,
        "audit_status": audit_status,
        "strict_pass": strict_pass,
        "claim_ledger_path": str(ledger_path.relative_to(ROOT)) if ledger_path.exists() else None,
        "evidence_bundle_path": str(evidence_path.relative_to(ROOT)) if evidence_path.exists() else None,
        "claim_count": len(claims),
        "claim_ledger_empty": len(claims) == 0,
        "claim_ledger_schema_status": ledger_status,
        "result_file_ref_count": len(evidence_refs),
        "result_file_refs_public_present": len(present_refs),
        "result_file_refs_missing": len(missing_refs),
        "result_file_refs_declared_unavailable": len(declared_unavailable_refs),
        "missing_result_file_refs_sample": missing_refs[:10],
        "issues": issues,
    }


def build_report() -> dict[str, Any]:
    rows = [audit_paper(path) for path in iter_paper_dirs()]
    count = len(rows)
    strict_pass_count = sum(1 for row in rows if row["strict_pass"])
    empty_ledgers = sum(1 for row in rows if row["claim_ledger_empty"])
    result_refs = sum(int(row["result_file_ref_count"]) for row in rows)
    present_refs = sum(int(row["result_file_refs_public_present"]) for row in rows)
    missing_refs = sum(int(row["result_file_refs_missing"]) for row in rows)
    featured = [row for row in rows if row["slug"] in FEATURED_SLUGS]
    return {
        "gate_name": STRICT_GATE_NAME,
        "gate_version": STRICT_GATE_VERSION,
        "gate_scope": "strict claim-ledger schema, non-empty claim evidence references, and public availability of evidence result_file references",
        "validated": [
            "claim_ledger_schema_parseable",
            "claims_non_empty",
            "claims_reference_evidence",
            "evidence_result_file_refs_public_or_declared_unavailable",
        ],
        "not_validated": [
            "scientific_correctness",
            "peer_review",
            "independent_replication",
            "statistical_power",
            "semantic_output_quality",
            "citation_accuracy",
        ],
        "count": count,
        "strict_claim_evidence_pass_count": strict_pass_count,
        "strict_claim_evidence_failed_count": count - strict_pass_count,
        "claim_ledgers_empty": empty_ledgers,
        "result_file_refs": result_refs,
        "result_file_refs_public_present": present_refs,
        "result_file_refs_missing": missing_refs,
        "featured_artifacts_checked": len(featured),
        "featured_artifacts_strict_pass_count": sum(1 for row in featured if row["strict_pass"]),
        "status": "strict_pass" if strict_pass_count == count and count else "blocked_audit_gaps",
        "gap_summary": "Claim ledgers are empty or result_file references are not publicly present; packaging/provenance lint must not be read as deep claim audit.",
        "rows": rows,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Strict claim/evidence audit",
        "",
        f"Strict claim/evidence passed: {report['strict_claim_evidence_pass_count']} / {report['count']}",
        "",
        "This audit is separate from the packaging/provenance lint. It requires non-empty claim ledgers with evidence references and public result-file references, or explicit unavailability metadata.",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- Empty claim ledgers: {report['claim_ledgers_empty']} / {report['count']}",
        f"- Evidence `result_files` references: {report['result_file_refs']}",
        f"- Publicly present result-file references: {report['result_file_refs_public_present']}",
        f"- Missing result-file references: {report['result_file_refs_missing']}",
        f"- Featured artifacts strict-pass count: {report['featured_artifacts_strict_pass_count']} / {report['featured_artifacts_checked']}",
        "",
        "## Validated",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["validated"])
    lines.extend(["", "## Not validated", ""])
    lines.extend(f"- `{item}`" for item in report["not_validated"])
    lines.extend(["", "## Rows", "", "| Paper | Strict pass | Claim count | Missing result refs | Issues |", "|---|---:|---:|---:|---|"])
    for row in report["rows"]:
        lines.append(
            f"| `{row['slug']}` | {row['strict_pass']} | {row['claim_count']} | {row['result_file_refs_missing']} | {json.dumps(row['issues'], sort_keys=True)} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit whether corpus claim ledgers and evidence result files satisfy the strict public contract.")
    parser.add_argument("--output-dir", type=Path, default=QUALITY)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when any artifact fails the strict audit.")
    args = parser.parse_args()

    report = build_report()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "claim_evidence_audit.json"
    md_path = args.output_dir / "claim_evidence_audit.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    print(json.dumps({
        "count": report["count"],
        "strict_claim_evidence_pass_count": report["strict_claim_evidence_pass_count"],
        "claim_ledgers_empty": report["claim_ledgers_empty"],
        "result_file_refs": report["result_file_refs"],
        "result_file_refs_missing": report["result_file_refs_missing"],
        "status": report["status"],
    }, indent=2, sort_keys=True))
    if args.strict and report["strict_claim_evidence_pass_count"] != report["count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
