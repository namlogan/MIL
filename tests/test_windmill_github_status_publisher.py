from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    status = 201

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(
            {
                "url": "https://api.github.com/repos/namlogan/MIL/statuses/abc123",
                "state": "success",
                "context": "ai-gate/final-review",
            }
        ).encode("utf-8")


class GitHubStatusPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.publisher = load_module(
            "windmill_github_commit_status",
            "f/mil/github_commit_status.py",
        )

    def test_build_status_payload_validates_github_state(self) -> None:
        payload = self.publisher.build_status_payload(
            state="success",
            context="ai-gate/final-review",
            description="APPROVE_MERGE",
            target_url="https://github.com/namlogan/MIL/pull/13",
        )

        self.assertEqual(payload["state"], "success")
        self.assertEqual(payload["context"], "ai-gate/final-review")
        self.assertEqual(payload["description"], "APPROVE_MERGE")

        with self.assertRaises(ValueError):
            self.publisher.build_status_payload(
                state="blocked",
                context="ai-gate/final-review",
                description="bad",
                target_url="https://github.com/namlogan/MIL/pull/13",
            )

    def test_script_pins_windmill_client_dependency_for_secret_access(self) -> None:
        script = (REPO_ROOT / "f" / "mil" / "github_commit_status.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("#requirements:", script)
        self.assertIn("#wmill", script)

    def test_publish_commit_status_uses_github_status_endpoint(self) -> None:
        seen = {}

        def fake_urlopen(request, timeout):
            seen["url"] = request.full_url
            seen["method"] = request.get_method()
            seen["body"] = json.loads(request.data.decode("utf-8"))
            seen["authorization"] = request.headers.get("Authorization")
            seen["timeout"] = timeout
            return FakeResponse()

        result = self.publisher.publish_commit_status(
            owner="namlogan",
            repo="MIL",
            sha="abc123",
            payload=self.publisher.build_status_payload(
                state="success",
                context="ai-gate/final-review",
                description="APPROVE_MERGE",
                target_url="https://github.com/namlogan/MIL/pull/13",
            ),
            token="test-token",
            urlopen=fake_urlopen,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(seen["method"], "POST")
        self.assertEqual(
            seen["url"],
            "https://api.github.com/repos/namlogan/MIL/statuses/abc123",
        )
        self.assertEqual(seen["body"]["state"], "success")
        self.assertEqual(seen["authorization"], "Bearer test-token")
        self.assertEqual(seen["timeout"], 30)

    def test_main_supports_dry_run_without_secret_access(self) -> None:
        result = self.publisher.main(
            {
                "owner": "namlogan",
                "repo": "MIL",
                "sha": "abc123",
                "state": "pending",
                "description": "gate queued",
                "target_url": "https://github.com/namlogan/MIL/pull/13",
                "dry_run": True,
            }
        )

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["payload"]["state"], "pending")
        self.assertNotIn("token", json.dumps(result).lower())


if __name__ == "__main__":
    unittest.main()
