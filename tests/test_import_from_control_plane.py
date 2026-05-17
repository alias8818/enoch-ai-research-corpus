from __future__ import annotations

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import_from_control_plane.py"
spec = importlib.util.spec_from_file_location("import_from_control_plane", SCRIPT)
assert spec and spec.loader
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


class ImportFromControlPlaneTests(unittest.TestCase):
    def test_dry_run_rejects_semantically_empty_evidence_artifacts(self) -> None:
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

        with (
            mock.patch.object(importer, "paper_detail", return_value=detail),
            mock.patch.object(importer, "artifact_content", side_effect=lambda base_url, token, pid, field: artifacts[field]),
        ):
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

        self.assertIn("evidence_bundle_path:missing_public_evidence_files", check["issues"])
        self.assertIn("claim_ledger_path:missing_claims", check["issues"])
        self.assertIn("manifest_path:missing_evidence_file_count", check["issues"])
        self.assertIs(check["semantic_evidence_gate"]["ok"], False)

    def test_dry_run_accepts_semantic_evidence_artifacts(self) -> None:
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

        with (
            mock.patch.object(importer, "paper_detail", return_value=detail),
            mock.patch.object(importer, "artifact_content", side_effect=lambda base_url, token, pid, field: artifacts[field]),
        ):
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

        self.assertEqual(check["issues"], [])
        self.assertIs(check["semantic_evidence_gate"]["ok"], True)


    def test_dry_run_rejects_claim_ledgers_that_require_review(self) -> None:
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
            "draft_markdown_path": "# Paper\n\nEvidence-linked but review-required draft.\n",
            "evidence_bundle_path": """{
              "public_evidence_files": [
                {"path": "evidence/run_notes.md", "source_path": "run_notes.md", "content": "measured result"}
              ]
            }""",
            "claim_ledger_path": """{
              "ledger_status": "claims_require_review",
              "unsupported_claim_count": 0,
              "claims": [
                {"claim": "measured result", "evidence_refs": [{"path": "evidence/run_notes.md"}]}
              ]
            }""",
            "manifest_path": """{
              "evidence_file_count": 1,
              "claim_count": 1,
              "claim_ledger_status": "claims_require_review"
            }""",
        }

        with (
            mock.patch.object(importer, "paper_detail", return_value=detail),
            mock.patch.object(importer, "artifact_content", side_effect=lambda base_url, token, pid, field: artifacts[field]),
        ):
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

        self.assertIn("claim_ledger_path:unexpected_ledger_status", check["issues"])
        self.assertIn("manifest_path:unexpected_claim_ledger_status", check["issues"])
        self.assertIs(check["semantic_evidence_gate"]["ok"], False)

    def test_live_import_refuses_to_write_semantically_empty_artifacts(self) -> None:
        paper_id = "paper:run:arxiv_draft"
        artifacts = {
            "draft_markdown_path": {"content": "# Paper\n\nEvidence-free draft.\n"},
            "evidence_bundle_path": {"content": "{}"},
            "claim_ledger_path": {"content": "{}"},
            "manifest_path": {"content": "{}"},
        }

        with TemporaryDirectory() as tmp_dir:
            paper_root = Path(tmp_dir) / "papers"
            stdout = io.StringIO()
            with (
                mock.patch.object(importer, "PAPERS", paper_root),
                mock.patch.object(importer, "existing_by_fingerprint", return_value={}),
                mock.patch.object(importer, "next_public_number", return_value=1),
                mock.patch.object(
                    importer,
                    "iter_rows",
                    return_value=iter([
                        {
                            "paper_id": paper_id,
                            "project_name": "Example Paper",
                            "project_id": "project-1",
                            "run_id": "run-1",
                            "paper_status": "publication_draft",
                            "review_status": "finalized",
                        }
                    ]),
                ),
                mock.patch.object(
                    importer,
                    "request_json",
                    side_effect=lambda base_url, token, path: artifacts[next(field for field in artifacts if path.endswith(f"/{field}"))],
                ),
                mock.patch.object(importer.sys, "argv", ["import_from_control_plane.py", "--control-url", "http://control", "--token", "token", "--limit", "1"]),
                contextlib.redirect_stdout(stdout),
            ):
                exit_code = importer.main()

            self.assertEqual(exit_code, 1)
            self.assertIn("semantic_evidence_check_failed", stdout.getvalue())
            self.assertFalse(list(paper_root.glob("*/paper.md")))
            self.assertFalse(list(paper_root.glob("*/metadata.json")))


if __name__ == "__main__":
    unittest.main()
