import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path

from apps.flange_qc_v2.asgi import app
from apps.flange_qc_v2.audit import AuditStore
from apps.flange_qc_v2.domain import InspectionSnapshot, ValidationError
from apps.flange_qc_v2.feedback import QcFeedback


class QcFeedbackContractTests(unittest.TestCase):
    def test_feedback_schema_exposes_shadow_evidence_contract(self) -> None:
        schema_path = Path("contracts/flange_qc_v2/feedback/qc_feedback.schema.json")

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        properties = schema["properties"]

        self.assertEqual(schema["title"], "Flange QC V2 QC Feedback")
        self.assertIn("feedback_type", schema["required"])
        self.assertIn("production_authority", schema["required"])
        self.assertEqual(
            set(properties["feedback_type"]["enum"]),
            {"CONFIRM_BLOCKED", "MARK_FALSE_POSITIVE", "MARK_FALSE_NEGATIVE", "REQUEST_REVIEW"},
        )
        self.assertEqual(properties["production_authority"]["const"], False)
        self.assertEqual(properties["authority_blockers"]["items"]["enum"], ["PRODUCTION_APPROVAL_REQUIRED"])

    def test_feedback_payload_is_shadow_evidence_without_production_authority(self) -> None:
        feedback = QcFeedback(
            feedback_id="fb-001",
            inspection_id="fqv2-phase2-synthetic-001",
            feedback_type="CONFIRM_BLOCKED",
            reviewer_id="qc-reviewer-1",
            note="Blocked state matches missing approval gates.",
            shadow_decision="BLOCKED",
            source_ref="https://github.com/namlogan/MIL/issues/81",
            created_at="2026-06-02T00:00:00Z",
        )

        payload = feedback.to_payload()
        parsed = QcFeedback.from_payload(payload)

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["feedback_type"], "CONFIRM_BLOCKED")
        self.assertEqual(payload["shadow_decision"], "BLOCKED")
        self.assertFalse(payload["production_authority"])
        self.assertEqual(payload["authority_blockers"], ["PRODUCTION_APPROVAL_REQUIRED"])
        self.assertEqual(parsed.feedback_id, "fb-001")

    def test_unknown_feedback_type_is_rejected_explicitly(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unknown feedback type"):
            QcFeedback(
                feedback_id="fb-bad",
                inspection_id="insp-001",
                feedback_type="APPROVE_PRODUCTION",
                reviewer_id="qc-reviewer-1",
                note="No.",
                shadow_decision="PASS",
                source_ref="issue",
                created_at="2026-06-02T00:00:00Z",
            )

    def test_invalid_schema_version_is_rejected_explicitly(self) -> None:
        payload = {
            "schema_version": "not-a-number",
            "feedback_id": "fb-bad-version",
            "inspection_id": "insp-001",
            "feedback_type": "REQUEST_REVIEW",
            "reviewer_id": "qc-reviewer-1",
            "note": "Bad schema version should be a domain validation error.",
            "shadow_decision": "BLOCKED",
            "source_ref": "issue",
            "created_at": "2026-06-02T00:00:00Z",
        }

        with self.assertRaisesRegex(ValidationError, "unsupported feedback schema_version"):
            QcFeedback.from_payload(payload)


class QcFeedbackAuditTests(unittest.TestCase):
    def test_append_and_fetch_feedback_for_inspection(self) -> None:
        snapshot = InspectionSnapshot.bootstrap_blocked(
            inspection_id="insp-feedback-001",
            product_code="611",
            reason_codes=["PRODUCT_SPEC_APPROVAL_MISSING"],
        )
        feedback = QcFeedback(
            feedback_id="fb-audit-001",
            inspection_id="insp-feedback-001",
            feedback_type="REQUEST_REVIEW",
            reviewer_id="qc-reviewer-1",
            note="Please review the blocked replay evidence.",
            shadow_decision="BLOCKED",
            source_ref="https://github.com/namlogan/MIL/issues/81",
            created_at="2026-06-02T00:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AuditStore(Path(tmpdir) / "audit.sqlite")
            store.initialize()
            store.append_inspection(snapshot)

            store.append_feedback(feedback)
            records = store.fetch_feedback("insp-feedback-001")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["feedback_id"], "fb-audit-001")
        self.assertEqual(records[0]["feedback_type"], "REQUEST_REVIEW")
        self.assertEqual(records[0]["payload"]["production_authority"], False)

    def test_feedback_for_missing_inspection_is_rejected_by_foreign_key(self) -> None:
        feedback = QcFeedback(
            feedback_id="fb-missing-inspection",
            inspection_id="missing-inspection",
            feedback_type="REQUEST_REVIEW",
            reviewer_id="qc-reviewer-1",
            note="Missing inspection should not accept feedback.",
            shadow_decision="BLOCKED",
            source_ref="https://github.com/namlogan/MIL/issues/81",
            created_at="2026-06-02T00:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AuditStore(Path(tmpdir) / "audit.sqlite")
            store.initialize()

            with self.assertRaisesRegex(ValidationError, "inspection does not exist"):
                store.append_feedback(feedback)


class QcFeedbackEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_audit_path = os.environ.pop("FLANGE_QC_V2_AUDIT_DB_PATH", None)

    def tearDown(self) -> None:
        os.environ.pop("FLANGE_QC_V2_AUDIT_DB_PATH", None)
        if self._previous_audit_path is not None:
            os.environ["FLANGE_QC_V2_AUDIT_DB_PATH"] = self._previous_audit_path

    def test_feedback_endpoint_validates_and_returns_shadow_evidence(self) -> None:
        payload = {
            "feedback_id": "fb-http-001",
            "inspection_id": "fqv2-phase2-synthetic-001",
            "feedback_type": "CONFIRM_BLOCKED",
            "reviewer_id": "qc-reviewer-1",
            "note": "Operator confirms blocked bootstrap evidence.",
            "shadow_decision": "BLOCKED",
            "source_ref": "https://github.com/namlogan/MIL/issues/81",
            "created_at": "2026-06-02T00:00:00Z",
        }
        body = json.dumps(payload).encode("utf-8")
        messages = []

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": "POST", "path": "/feedback"}
        asyncio.run(app(scope, receive, send))

        start = messages[0]
        response = json.loads(messages[1]["body"].decode("utf-8"))

        self.assertEqual(start["status"], 200)
        self.assertEqual(response["feedback_type"], "CONFIRM_BLOCKED")
        self.assertEqual(response["inspection_id"], "fqv2-phase2-synthetic-001")
        self.assertEqual(response["shadow_decision"], "BLOCKED")
        self.assertEqual(response["authority_blockers"], ["PRODUCTION_APPROVAL_REQUIRED"])
        self.assertFalse(response["production_authority"])

    def test_feedback_endpoint_persists_shadow_evidence_when_audit_db_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.sqlite"
            os.environ["FLANGE_QC_V2_AUDIT_DB_PATH"] = str(audit_path)

            self._call_json_endpoint("GET", "/inspection/replay")
            response = self._call_json_endpoint(
                "POST",
                "/feedback",
                {
                    "feedback_id": "fb-http-persist-001",
                    "inspection_id": "fqv2-phase2-synthetic-001",
                    "feedback_type": "CONFIRM_BLOCKED",
                    "reviewer_id": "qc-reviewer-1",
                    "note": "Persist this operator feedback to the audit DB.",
                    "shadow_decision": "BLOCKED",
                    "source_ref": "https://github.com/namlogan/MIL/issues/97",
                    "created_at": "2026-06-02T00:00:00Z",
                },
            )

            store = AuditStore(audit_path)
            inspection = store.fetch_inspection("fqv2-phase2-synthetic-001")
            records = store.fetch_feedback("fqv2-phase2-synthetic-001")

        self.assertEqual(response["status"], 200)
        self.assertTrue(response["body"]["audit"]["persisted"])
        self.assertEqual(response["body"]["audit"]["feedback_count"], 1)
        self.assertIsNotNone(inspection)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["feedback_id"], "fb-http-persist-001")
        self.assertFalse(records[0]["payload"]["production_authority"])

    def test_feedback_endpoint_rejects_invalid_payload(self) -> None:
        payload = {
            "feedback_id": "fb-http-bad",
            "inspection_id": "fqv2-phase2-synthetic-001",
            "feedback_type": "APPROVE_PRODUCTION",
            "reviewer_id": "qc-reviewer-1",
            "note": "Trying to approve production from QC feedback is not allowed.",
            "shadow_decision": "PASS",
            "source_ref": "https://github.com/namlogan/MIL/issues/81",
            "created_at": "2026-06-02T00:00:00Z",
        }
        body = json.dumps(payload).encode("utf-8")
        messages = []

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": "POST", "path": "/feedback"}
        asyncio.run(app(scope, receive, send))

        start = messages[0]
        response = json.loads(messages[1]["body"].decode("utf-8"))

        self.assertEqual(start["status"], 400)
        self.assertIn("unknown feedback type", response["detail"])

    def test_invalid_feedback_is_not_persisted_when_audit_db_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.sqlite"
            os.environ["FLANGE_QC_V2_AUDIT_DB_PATH"] = str(audit_path)
            self._call_json_endpoint("GET", "/inspection/replay")

            response = self._call_json_endpoint(
                "POST",
                "/feedback",
                {
                    "feedback_id": "fb-http-bad-persist",
                    "inspection_id": "fqv2-phase2-synthetic-001",
                    "feedback_type": "APPROVE_PRODUCTION",
                    "reviewer_id": "qc-reviewer-1",
                    "note": "This must not create audit feedback.",
                    "shadow_decision": "PASS",
                    "source_ref": "https://github.com/namlogan/MIL/issues/97",
                    "created_at": "2026-06-02T00:00:00Z",
                },
            )
            store = AuditStore(audit_path)
            records = store.fetch_feedback("fqv2-phase2-synthetic-001")

        self.assertEqual(response["status"], 400)
        self.assertEqual(records, [])

    def _call_json_endpoint(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        messages = []

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": method, "path": path}
        asyncio.run(app(scope, receive, send))

        return {
            "status": messages[0]["status"],
            "body": json.loads(messages[1]["body"].decode("utf-8")),
        }


if __name__ == "__main__":
    unittest.main()
