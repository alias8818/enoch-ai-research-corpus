#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
QUALITY = ROOT / "quality"
FAILURES: list[str] = []

STALE_RELEASE_COUNT = re.compile(r"\b120\s+(?:AI-generated|generated research|artifacts)|120/120[^\n]{0,120}(?:quality gate|packaging|artifact|corpus|release)|(?:quality gate|packaging|artifact|corpus|release)[^\n]{0,120}120/120", re.I)
UNSCOPED_QUALITY_GATE = re.compile(r"quality gate pass", re.I)
PACKAGING_PASS = re.compile(r"(?:Packaging/provenance(?: lint)?(?: passed| pass)?:?\s*\d+\s*/\s*\d+|\d+\s*/\s*\d+[^\n]{0,80}packaging/provenance(?: lint)?)", re.I)
AUDITED_CLAIMS = re.compile(r"(?<!un)audited claims", re.I)
PRIVATE_PATH_ROOT = re.compile(r"(?:/home/jeremy|/var/lib/enoch|/opt/enoch|/etc/enoch|/mnt/usb|/root)\b")
PRIVATE_OR_LOOPBACK_IPV4 = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|127\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b"
)
PRIVATE_NETWORK_DETAIL = re.compile(
    r"\b(?:enoch-core\.exe\.xyz|ping-responsive|ssh-like|non-interactive\s+ssh|remote\s+peers?)\b",
    re.I,
)

PUBLIC_EXTRA_FILES = [ROOT / "README.md", PAPERS / "index.md"]


def fail(message: str) -> None:
    FAILURES.append(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def line_for(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def public_markdown_files() -> list[Path]:
    files = PUBLIC_EXTRA_FILES[:]
    files.extend(sorted(QUALITY.glob("*.md")))
    files.extend(sorted(PAPERS.glob("*/paper.md")))
    return [path for path in files if path.exists()]


def public_text_files() -> list[Path]:
    files = public_markdown_files()
    files.extend(sorted(PAPERS.glob("*/evidence/public_paper.md")))
    files.extend(sorted(PAPERS.glob("*/claim_ledger.json")))
    files.extend(sorted(QUALITY.glob("*.json")))
    files.append(PAPERS / "index.json")
    return [path for path in files if path.exists()]


def check_private_details_are_redacted() -> None:
    for path in public_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for pattern in (
            PRIVATE_PATH_ROOT,
            PRIVATE_OR_LOOPBACK_IPV4,
            PRIVATE_NETWORK_DETAIL,
        ):
            for match in pattern.finditer(text):
                fail(
                    f"{rel}:{line_for(text, match.start())} private detail leaked: {match.group(0)!r}"
                )


def check_public_text() -> None:
    for path in public_markdown_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for match in STALE_RELEASE_COUNT.finditer(text):
            fail(f"{rel}:{line_for(text, match.start())} stale Enoch release count context: {match.group(0)!r}")
        for match in UNSCOPED_QUALITY_GATE.finditer(text):
            window = text[max(0, match.start() - 120):match.end() + 160].lower()
            if "packaging/provenance" not in window:
                fail(f"{rel}:{line_for(text, match.start())} unscoped quality gate wording: {match.group(0)!r}")


def check_quality_report_header() -> None:
    path = QUALITY / "quality_report.md"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    first20 = "\n".join(lines[:20]).lower()
    audit = load_json(QUALITY / "claim_evidence_audit.json")
    expected_strict = f"{audit.get('strict_claim_evidence_pass_count')} / {audit.get('count')}"
    expected_packaging = f"{audit.get('count')} / {audit.get('count')}"
    required = ["packaging/provenance lint", expected_packaging, "strict claim/evidence", expected_strict, "not validated"]
    for phrase in required:
        if phrase not in first20:
            fail(f"quality/quality_report.md first 20 lines missing {phrase!r}")


def check_packaging_pass_has_strict_context() -> None:
    audit = load_json(QUALITY / "claim_evidence_audit.json")
    expected_strict = rf"{audit.get('strict_claim_evidence_pass_count')}\s*/\s*{audit.get('count')}"
    for path in [QUALITY / "quality_report.md", QUALITY / "packaging_provenance_report.md", ROOT / "README.md"]:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for match in PACKAGING_PASS.finditer(text):
            window = text[max(0, match.start() - 300):match.end() + 300].lower()
            if "packaging/provenance lint" not in window or "strict claim/evidence" not in window or not re.search(expected_strict, window):
                fail(f"{rel}:{line_for(text, match.start())} packaging pass lacks nearby strict audit context")


def check_index_claim_columns() -> None:
    text = (PAPERS / "index.md").read_text(encoding="utf-8", errors="replace")
    if "Claims yes" in text or re.search(r"\|\s*Claims\s*\|", text):
        fail("papers/index.md still has generic Claims column/yes wording")
    audit = load_json(QUALITY / "claim_evidence_audit.json")
    rows = {row["slug"]: row for row in audit.get("rows", [])}
    for slug, audit_row in rows.items():
        if audit_row.get("claim_count") == 0:
            expected = f"| 0 | false | {audit_row.get('result_file_refs_missing')} |"
            if expected not in text:
                fail(f"papers/index.md missing expected audit cells for {slug}: {expected}")


def check_audited_claims_against_ledgers() -> None:
    for paper in sorted(PAPERS.glob("*/paper.md")):
        ledger_path = paper.parent / "claim_ledger.json"
        if not ledger_path.exists():
            continue
        ledger = load_json(ledger_path)
        claims = ledger.get("claims") if isinstance(ledger, dict) else None
        if isinstance(claims, list) and not claims:
            text = paper.read_text(encoding="utf-8", errors="replace")
            for match in AUDITED_CLAIMS.finditer(text):
                fail(f"{paper.relative_to(ROOT)}:{line_for(text, match.start())} says audited claims while ledger claims=[]")


def check_absolute_path_refs_do_not_pass() -> None:
    module_path = ROOT / "scripts" / "audit_claim_evidence_contract.py"
    spec = importlib.util.spec_from_file_location("claim_evidence_audit", module_path)
    if spec is None or spec.loader is None:
        fail(f"cannot load {module_path}")
        return
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        paper_dir = tmp_root / "paper"
        paper_dir.mkdir()
        private_file = tmp_root / "private-result.json"
        private_file.write_text("{}\n", encoding="utf-8")
        if audit.ref_exists(paper_dir, str(private_file)):
            fail("strict audit ref_exists accepted an absolute local path")
        unavailable = {
            "unavailable_result_files": [
                {
                    "path": str(private_file),
                    "reason": "private",
                    "sha256": "0" * 64,
                    "bytes": 3,
                    "public_surrogate": "quality/claim_evidence_audit.md",
                }
            ]
        }
        if not audit.is_declared_unavailable(unavailable, str(private_file)):
            fail("strict audit rejected explicit absolute/private unavailability metadata")
        incomplete = {"unavailable_result_files": [{"path": str(private_file), "reason": "private"}]}
        if audit.is_declared_unavailable(incomplete, str(private_file)):
            fail("strict audit accepted private unavailability metadata without hash/bytes/surrogate")
        string_only = {"unavailable_result_files": [str(private_file)]}
        if audit.is_declared_unavailable(string_only, str(private_file)):
            fail("strict audit accepted string-only unavailable_result_files without hash/bytes/surrogate")


def main() -> int:
    check_public_text()
    check_private_details_are_redacted()
    check_quality_report_header()
    check_packaging_pass_has_strict_context()
    check_index_claim_columns()
    check_audited_claims_against_ledgers()
    check_absolute_path_refs_do_not_pass()
    if FAILURES:
        for item in FAILURES:
            print(f"FAIL {item}")
        return 1
    print("PASS public trust surfaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
