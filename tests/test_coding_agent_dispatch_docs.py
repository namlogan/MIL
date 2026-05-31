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


if __name__ == "__main__":
    unittest.main()
