import asyncio
import unittest
from pathlib import Path

from apps.flange_qc_v2.asgi import app


REPO_ROOT = Path(__file__).resolve().parents[2]
HMI_HTML = REPO_ROOT / "apps/flange_qc_v2/static/hmi.html"


class HmiScreenTests(unittest.TestCase):
    def test_hmi_endpoint_returns_operator_screen_html(self) -> None:
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "method": "GET", "path": "/hmi"}
        asyncio.run(app(scope, receive, send))

        start = messages[0]
        body = messages[1]["body"].decode("utf-8")
        headers = dict(start["headers"])

        self.assertEqual(start["status"], 200)
        self.assertEqual(headers[b"content-type"], b"text/html; charset=utf-8")
        self.assertIn("<title>Flange QC HMI</title>", body)
        self.assertIn('rel="icon"', body)
        self.assertIn('href="data:,"', body)
        self.assertIn('id="decision"', body)
        self.assertIn('id="reason-list"', body)
        self.assertIn('id="measurements"', body)
        self.assertIn('id="phase-results"', body)
        self.assertIn('id="artifact-intake-status"', body)
        self.assertIn('id="refresh-replay"', body)
        self.assertIn('id="feedback-form"', body)
        self.assertIn('id="feedback-status"', body)

    def test_hmi_html_binds_to_websocket_snapshot_fields(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn("new WebSocket", html)
        self.assertIn("/ws/inspection", html)
        self.assertIn("renderSnapshot", html)
        self.assertIn("payload.reason_codes", html)
        self.assertIn("payload.measurements", html)
        self.assertIn("payload.phase_results", html)
        self.assertIn("renderPhaseResults", html)
        self.assertIn("renderRuleResults", html)
        self.assertIn("payload.observations", html)
        self.assertIn("PRODUCT_SPEC_APPROVAL_MISSING", html)

    def test_hmi_html_renders_sop_phase_results_drilldown(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn('aria-label="SOP phase results"', html)
        self.assertIn('id="phase-results"', html)
        self.assertIn("phase-result-card", html)
        self.assertIn("rule-result-list", html)
        self.assertIn("No phase results", html)
        self.assertIn("authority_blockers", html)
        self.assertIn("production_authority", html)
        self.assertIn("M1-SOP-6.4-PUNCH-MARK-001", html)

    def test_hmi_html_renders_signal_first_qc_tablet_viewport(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn('aria-label="QC tablet operating viewport"', html)
        self.assertIn('id="qc-tablet-viewport"', html)
        self.assertIn('id="measurement-strip"', html)
        self.assertIn('id="operator-state-banner"', html)
        self.assertIn('id="operator-state-label"', html)
        self.assertIn('id="operator-state-action"', html)
        self.assertIn('id="inspection-image-panel"', html)
        self.assertIn('id="suspect-overlay-layer"', html)
        self.assertIn('id="suspect-region-label"', html)
        self.assertIn('id="alarm-feedback-actions"', html)
        self.assertIn('id="alarm-correct"', html)
        self.assertIn('id="alarm-false"', html)
        self.assertIn("Alert correct", html)
        self.assertIn("False alarm", html)
        self.assertIn("Next product", html)
        self.assertIn("Details", html)

    def test_hmi_html_defines_qc_tablet_state_overlay_and_feedback_helpers(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn("renderQcTabletViewport", html)
        self.assertIn("mapOperatorState", html)
        self.assertIn("renderMeasurementStrip", html)
        self.assertIn("renderInspectionImagePanel", html)
        self.assertIn("renderAlarmFeedbackActions", html)
        self.assertIn("submitAlarmFeedback", html)
        self.assertIn("applySuspectOverlay", html)
        self.assertIn("hasActionableObservation", html)
        self.assertIn("measurementChipState", html)
        self.assertIn('data-operator-state="pass"', html)
        self.assertIn('data-operator-state="check"', html)
        self.assertIn('data-operator-state="review"', html)
        self.assertIn("PASS", html)
        self.assertIn("CHECK", html)
        self.assertIn("REVIEW", html)
        self.assertIn("Continue", html)
        self.assertIn("Inspect suspected area", html)
        self.assertIn("Wait / review", html)
        self.assertIn("MARK_FALSE_POSITIVE", html)
        self.assertIn("CONFIRM_BLOCKED", html)

    def test_hmi_html_renders_artifact_intake_readiness_panel(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn('aria-label="Artifact intake readiness"', html)
        self.assertIn('id="artifact-intake-status"', html)
        self.assertIn('id="artifact-intake-artifacts"', html)
        self.assertIn("fetchArtifactIntakeStatus", html)
        self.assertIn("renderArtifactIntakeStatus", html)
        self.assertIn('fetch("/artifact-intake/status"', html)
        self.assertIn("FLANGE_QC_V2_ARTIFACT_INTAKE_DIR", html)
        self.assertIn("shadow_model_integration_issue", html)
        self.assertIn("live_camera_implementation_issue", html)
        self.assertIn("dataset_manifest", html)

    def test_hmi_html_renders_detector_observation_detail_panel(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn('aria-label="Detector observations"', html)
        self.assertIn('id="detector-observations"', html)
        self.assertIn("renderDetectorObservations", html)
        self.assertIn("observation-card", html)
        self.assertIn("No detector observations", html)
        self.assertIn("model_ref", html)
        self.assertIn("evidence_ref", html)
        self.assertIn("confidence", html)
        self.assertIn("bbox", html)

    def test_hmi_html_renders_detector_shadow_status_panel(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn('aria-label="Detector shadow status"', html)
        self.assertIn('id="detector-shadow-status"', html)
        self.assertIn('id="detector-shadow-ready"', html)
        self.assertIn('id="detector-shadow-adapter"', html)
        self.assertIn('id="detector-shadow-model-ref"', html)
        self.assertIn('id="detector-shadow-labels"', html)
        self.assertIn('id="detector-shadow-approval-status"', html)
        self.assertIn('id="detector-shadow-authority-blockers"', html)
        self.assertIn("fetchDetectorShadowStatus", html)
        self.assertIn("renderDetectorShadowStatus", html)
        self.assertIn('fetch("/detector/shadow/status"', html)
        self.assertIn("manifest-detector", html)
        self.assertIn("MODEL_APPROVAL_REQUIRED", html)

    def test_hmi_html_binds_operator_feedback_form_to_shadow_endpoint(self) -> None:
        html = HMI_HTML.read_text(encoding="utf-8")

        self.assertIn('name="reviewer_id"', html)
        self.assertIn('name="feedback_type"', html)
        self.assertIn('name="note"', html)
        self.assertIn("fetchReplaySnapshot", html)
        self.assertIn('fetch("/inspection/replay"', html)
        self.assertIn("submitFeedback", html)
        self.assertIn('fetch("/feedback"', html)
        self.assertIn("result.audit.persisted", html)
        self.assertIn("auditStatus", html)
        self.assertIn("production_authority", html)
        self.assertIn("authority_blockers", html)


if __name__ == "__main__":
    unittest.main()
