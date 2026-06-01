from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def auto_build_issue_payload(labels: list[str] | None = None) -> dict:
    return {
        "github_event": "issues",
        "delivery": "delivery-auto-1",
        "payload": {
            "action": "labeled",
            "repository": {"full_name": "namlogan/MIL"},
            "issue": {
                "number": 41,
                "title": "MIL-041 Auto dispatcher smoke",
                "body": "\n".join(
                    [
                        "### Task ID",
                        "MIL-041",
                        "",
                        "### User or business goal",
                        "Run the Codex worker automatically from a routed webhook.",
                        "",
                        "### Acceptance criteria",
                        "- Dispatcher invokes the local Codex worker runner.",
                        "- Worker prompt includes Augment codebase context.",
                        "",
                        "### Allowed files and out-of-scope files",
                        "Allowed:",
                        "- docs/**",
                        "",
                        "Out of scope:",
                        "- secrets/**",
                        "",
                        "### Required checks",
                        "- git diff --check",
                        "",
                        "### Restricted change check",
                        "- [x] none of the above",
                        "",
                        "### Rollback note",
                        "Close the generated PR.",
                    ]
                ),
                "labels": [{"name": label} for label in (labels or ["agent:auto-build"])],
            },
        },
    }


class AutoDispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dispatcher = load_module(
            "auto_dispatcher",
            "scripts/agent-flow/auto_dispatcher.py",
        )

    def test_requires_explicit_auto_build_label(self) -> None:
        result = self.dispatcher.dispatch_request(
            auto_build_issue_payload(labels=["agent:build"]),
            repo_root=REPO_ROOT,
            execute_agent=True,
            push=True,
            open_pr=True,
            runner=lambda **kwargs: self.fail("runner should not be called"),
        )

        self.assertEqual(result["decision"], "AUTO_DISPATCH_IGNORED")
        self.assertIn("agent:auto-build", result["reason"])

    def test_dispatches_auto_build_to_runner_with_augment_context(self) -> None:
        captured: dict = {}

        def fake_runner(**kwargs):
            captured.update(kwargs)
            return {
                "status": "CODEX_WORKER_COMPLETED",
                "git": {"pushed": True, "pr_url": "https://github.com/namlogan/MIL/pull/41"},
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.dispatcher.dispatch_request(
                auto_build_issue_payload(),
                repo_root=REPO_ROOT,
                execute_agent=True,
                push=True,
                open_pr=True,
                runner=fake_runner,
                lock_root=Path(tmpdir),
            )

        self.assertEqual(result["decision"], "AUTO_DISPATCH_COMPLETED")
        self.assertTrue(captured["execute_agent"])
        self.assertTrue(captured["push"])
        self.assertTrue(captured["open_pr"])
        self.assertEqual(captured["task"]["task_id"], "MIL-041")
        self.assertIn("docs/**", captured["task"]["allowed_files"])
        augment_context = captured["task"]["augment_context"]
        self.assertTrue(augment_context)
        self.assertIn("augment://mcp/mil-auggie-local/codebase-retrieval", augment_context[0]["source_uri"])
        self.assertIn("git diff --check", augment_context[0]["summary"])

    def test_dispatch_preserves_preloaded_augment_context_for_runner(self) -> None:
        captured: dict = {}

        def fake_runner(**kwargs):
            captured.update(kwargs)
            return {"status": "DRY_RUN", "git": {"pushed": False, "pr_url": ""}}

        with tempfile.TemporaryDirectory() as tmpdir:
            request = {
                **auto_build_issue_payload(),
                "augment_context": [
                    {
                        "source_uri": "augment://mcp/mil-auggie-local/codebase-retrieval/result",
                        "summary": "Preloaded dispatcher context for auto_dispatcher.py.",
                    }
                ],
            }
            result = self.dispatcher.dispatch_request(
                request,
                repo_root=REPO_ROOT,
                dry_run=True,
                runner=fake_runner,
                lock_root=Path(tmpdir),
            )

        self.assertEqual(result["decision"], "AUTO_DISPATCH_COMPLETED")
        summaries = [item["summary"] for item in captured["task"]["augment_context"]]
        self.assertTrue(any("Preloaded dispatcher context" in summary for summary in summaries))
        self.assertTrue(any("Before implementation, use Augment MCP" in summary for summary in summaries))

    def test_dispatch_can_preload_augment_context_before_runner(self) -> None:
        captured: dict = {}
        provider_calls: list[dict] = []

        def fake_provider(**kwargs):
            provider_calls.append(kwargs)
            return {
                "ok": True,
                "context_pack": [
                    {
                        "source_uri": "augment://mcp/mil-auggie-local/codebase-retrieval/result",
                        "summary": "Control-plane Augment result for docs and runner contracts.",
                    }
                ],
            }

        def fake_runner(**kwargs):
            captured.update(kwargs)
            return {"status": "DRY_RUN", "git": {"pushed": False, "pr_url": ""}}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.dispatcher.dispatch_request(
                auto_build_issue_payload(),
                repo_root=REPO_ROOT,
                dry_run=True,
                runner=fake_runner,
                lock_root=Path(tmpdir),
                preload_augment_context=True,
                augment_context_provider=fake_provider,
            )

        self.assertEqual(result["decision"], "AUTO_DISPATCH_COMPLETED")
        self.assertEqual(len(provider_calls), 1)
        self.assertIn("MIL-041 Auto dispatcher smoke", provider_calls[0]["query"])
        summaries = [item["summary"] for item in captured["task"]["augment_context"]]
        self.assertTrue(any("Control-plane Augment result" in summary for summary in summaries))
        self.assertEqual(
            result["augment_context_preload"]["context_pack"][0]["summary"],
            "Control-plane Augment result for docs and runner contracts.",
        )

    def test_dispatch_claims_task_once(self) -> None:
        calls: list[dict] = []

        def fake_runner(**kwargs):
            calls.append(kwargs)
            return {"status": "DRY_RUN", "git": {"pushed": False, "pr_url": ""}}

        with tempfile.TemporaryDirectory() as tmpdir:
            first = self.dispatcher.dispatch_request(
                auto_build_issue_payload(),
                repo_root=REPO_ROOT,
                dry_run=True,
                runner=fake_runner,
                lock_root=Path(tmpdir),
            )
            second = self.dispatcher.dispatch_request(
                auto_build_issue_payload(),
                repo_root=REPO_ROOT,
                dry_run=True,
                runner=fake_runner,
                lock_root=Path(tmpdir),
            )

        self.assertEqual(first["decision"], "AUTO_DISPATCH_COMPLETED")
        self.assertEqual(second["decision"], "AUTO_DISPATCH_IGNORED")
        self.assertIn("already claimed", second["reason"])
        self.assertEqual(len(calls), 1)

    def test_self_test_is_repeatable(self) -> None:
        self.dispatcher._self_test()
        self.dispatcher._self_test()

    def test_blocks_when_plan_to_pr_is_not_ready(self) -> None:
        request = auto_build_issue_payload()
        request["payload"]["issue"]["body"] = "\n".join(
            [
                "### Task ID",
                "MIL-042",
                "",
                "### User or business goal",
                "Missing file scope should block.",
                "",
                "### Acceptance criteria",
                "- Dispatcher blocks.",
                "",
                "### Required checks",
                "- git diff --check",
                "",
                "### Restricted change check",
                "- [x] none of the above",
                "",
                "### Rollback note",
                "Close issue.",
            ]
        )

        result = self.dispatcher.dispatch_request(
            request,
            repo_root=REPO_ROOT,
            execute_agent=True,
            push=True,
            open_pr=True,
            runner=lambda **kwargs: self.fail("runner should not be called"),
        )

        self.assertEqual(result["decision"], "AUTO_DISPATCH_BLOCKED")
        self.assertIn("allowed_files", result["reasons"][0])


if __name__ == "__main__":
    unittest.main()
