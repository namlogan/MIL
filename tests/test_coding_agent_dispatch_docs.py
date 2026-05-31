from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class CodingAgentDispatchDocsTests(unittest.TestCase):
    def test_dispatch_flow_is_documented(self) -> None:
        flow = (
            REPO_ROOT / ".windmill" / "flows" / "coding_agent_dispatch.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Select and launch the coding agent", flow)
        self.assertIn("codex", flow)
        self.assertIn("only supported coding lane", flow)
        self.assertNotIn("auggie_supervised", flow)
        self.assertIn("agent/<issue-id>-<slug>", flow)
        self.assertIn("do not auto-merge", flow)

    def test_operating_model_includes_coding_dispatch_before_pr(self) -> None:
        model = (REPO_ROOT / "docs" / "agent-operating-model.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("coding-agent dispatch -> implementation branch -> pull request", model)

    def test_ai_factory_requires_coding_dispatch(self) -> None:
        config = (REPO_ROOT / ".ai-factory" / "config.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("require_coding_agent_dispatch: true", config)
        self.assertIn("augment_context:", config)
        self.assertNotIn("auggie_supervised:", config)

    def test_active_docs_match_augmented_codex_only_model(self) -> None:
        active_docs = [
            REPO_ROOT / "README.md",
            REPO_ROOT / ".windmill" / "flows" / "issue_to_plan.md",
            REPO_ROOT / ".windmill" / "flows" / "plan_to_pr.md",
            REPO_ROOT / ".windmill" / "flows" / "fix_ci_or_review.md",
            REPO_ROOT / ".windmill" / "flows" / "pr_quality_gate.md",
            REPO_ROOT / "docs" / "windmill-setup.md",
        ]
        forbidden_phrases = [
            "Auggie is the advisory review and diagnosis worker",
            "auggie.validate_plan",
            "auggie.review",
            "auggie.diagnose",
            "supervised Auggie developer worker",
            "actual Codex and Auggie CLIs or SDKs",
        ]

        for path in active_docs:
            with self.subTest(path=path):
                contents = path.read_text(encoding="utf-8")
                self.assertNotIn("auggie_supervised_developer", contents)
                for phrase in forbidden_phrases:
                    self.assertNotIn(phrase, contents)

        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Codex is the only implementation and test worker", readme)
        self.assertIn("Augment provides codebase index/context", readme)


if __name__ == "__main__":
    unittest.main()
