from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import_from_control_plane.py"
spec = importlib.util.spec_from_file_location("import_from_control_plane", SCRIPT)
assert spec and spec.loader
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


def test_dry_run_rejects_semantically_empty_evidence_artifacts(monkeypatch):
    paper_id = "paper:run:arxiv_draft"

    detail = {
        "paper": {
            "paper_id": paper_id,
            "paper_status": "publication_draft",
            "review_status": "finalized",
            "finalization_package_path": "papers/example/paper_manifest.json",
        },
        "events": [
            {"event_type": "paper.drafted"},
            {"event_type": "paper_review.finalization_package_prepared"},
        ],
    }
    artifacts = {
        "draft_markdown_path": "# Paper\n\nEvidence-free draft.\n",
        "evidence_bundle_path": "{}",
        "claim_ledger_path": "{}",
        "manifest_path": "{}",
    }

    monkeypatch.setattr(importer, "paper_detail", lambda base_url, token, pid: detail)
    monkeypatch.setattr(importer, "artifact_content", lambda base_url, token, pid, field: artifacts[field])

    check = importer.dry_run_check(
        "http://control",
        "token",
        row={"paper_id": paper_id, "project_name": "Example"},
        paper_id=paper_id,
        paper_dir=ROOT / "papers" / "example-test",
        match_kind="new",
        redactions={paper_id},
        expected_paper_status="publication_draft",
        expected_review_status="finalized",
    )

    assert "evidence_bundle_path:missing_public_evidence_files" in check["issues"]
    assert "claim_ledger_path:missing_claims" in check["issues"]
    assert "manifest_path:missing_evidence_file_count" in check["issues"]
    assert check["semantic_evidence_gate"]["ok"] is False


def test_dry_run_accepts_semantic_evidence_artifacts(monkeypatch):
    paper_id = "paper:run:arxiv_draft"

    detail = {
        "paper": {
            "paper_id": paper_id,
            "paper_status": "publication_draft",
            "review_status": "finalized",
            "finalization_package_path": "papers/example/paper_manifest.json",
        },
        "events": [
            {"event_type": "paper.drafted"},
            {"event_type": "paper_review.finalization_package_prepared"},
        ],
    }
    artifacts = {
        "draft_markdown_path": "# Paper\n\nEvidence-linked draft.\n",
        "evidence_bundle_path": """{
          "public_evidence_files": [
            {"path": "evidence/run_notes.md", "source_path": "run_notes.md", "content": "measured result"}
          ]
        }""",
        "claim_ledger_path": """{
          "ledger_status": "claims_reference_evidence",
          "unsupported_claim_count": 0,
          "claims": [
            {"claim": "measured result", "evidence_refs": [{"path": "evidence/run_notes.md"}]}
          ]
        }""",
        "manifest_path": """{
          "evidence_file_count": 1,
          "claim_count": 1,
          "claim_ledger_status": "claims_reference_evidence"
        }""",
    }

    monkeypatch.setattr(importer, "paper_detail", lambda base_url, token, pid: detail)
    monkeypatch.setattr(importer, "artifact_content", lambda base_url, token, pid, field: artifacts[field])

    check = importer.dry_run_check(
        "http://control",
        "token",
        row={"paper_id": paper_id, "project_name": "Example"},
        paper_id=paper_id,
        paper_dir=ROOT / "papers" / "example-test",
        match_kind="new",
        redactions={paper_id},
        expected_paper_status="publication_draft",
        expected_review_status="finalized",
    )

    assert check["issues"] == []
    assert check["semantic_evidence_gate"]["ok"] is True


def test_live_import_refuses_to_write_semantically_empty_artifacts(monkeypatch, tmp_path, capsys):
    paper_id = "paper:run:arxiv_draft"
    paper_root = tmp_path / "papers"
    artifacts = {
        "draft_markdown_path": {"content": "# Paper\n\nEvidence-free draft.\n"},
        "evidence_bundle_path": {"content": "{}"},
        "claim_ledger_path": {"content": "{}"},
        "manifest_path": {"content": "{}"},
    }

    monkeypatch.setattr(importer, "PAPERS", paper_root)
    monkeypatch.setattr(importer, "existing_by_fingerprint", lambda: {})
    monkeypatch.setattr(importer, "next_public_number", lambda: 1)
    monkeypatch.setattr(
        importer,
        "iter_rows",
        lambda *args, **kwargs: iter([
            {
                "paper_id": paper_id,
                "project_name": "Example Paper",
                "project_id": "project-1",
                "run_id": "run-1",
                "paper_status": "publication_draft",
                "review_status": "finalized",
            }
        ]),
    )
    monkeypatch.setattr(
        importer,
        "request_json",
        lambda base_url, token, path: artifacts[next(field for field in artifacts if path.endswith(f"/{field}"))],
    )
    monkeypatch.setattr(
        importer.sys,
        "argv",
        ["import_from_control_plane.py", "--control-url", "http://control", "--token", "token", "--limit", "1"],
    )

    assert importer.main() == 1
    output = capsys.readouterr().out
    assert "semantic_evidence_check_failed" in output
    assert not list(paper_root.glob("*/paper.md"))
    assert not list(paper_root.glob("*/metadata.json"))
