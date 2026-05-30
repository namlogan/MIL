from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMAND_DIR = REPO_ROOT / ".augment" / "commands"
COMMANDS = (
    "mil-morning-triage.md",
    "mil-plan-review.md",
    "mil-pr-review.md",
    "mil-ci-diagnose.md",
    "mil-handoff.md",
)
ALLOWED_VERDICTS = (
    "AUGMENT_REVIEW_PASS",
    "AUGMENT_REVIEW_NOTES",
    "AUGMENT_REVIEW_CHANGES_RECOMMENDED",
    "AUGMENT_REVIEW_BLOCKED",
)
SENSITIVE_LITERALS = (
    "accessToken",
    "AUGMENT_SESSION_AUTH={",
    "AUGMENT_MCP_TOKEN=",
    "AUGMENT_API_TOKEN=",
)


class AuggieSupervisedLaneTests(unittest.TestCase):
    def test_command_pack_exists_with_required_verdicts(self) -> None:
        for command in COMMANDS:
            with self.subTest(command=command):
                content = (COMMAND_DIR / command).read_text(encoding="utf-8")

                self.assertIn("Codex supervision", content)
                self.assertIn("Do not", content)
                for verdict in ALLOWED_VERDICTS:
                    self.assertIn(verdict, content)

    def test_command_pack_does_not_embed_secret_shapes(self) -> None:
        docs = [
            *(COMMAND_DIR / command for command in COMMANDS),
            REPO_ROOT / "docs" / "auggie-human-loop-runbook.md",
            REPO_ROOT / ".windmill" / "flows" / "auggie_supervised_advisory.md",
        ]

        for path in docs:
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                content = path.read_text(encoding="utf-8")
                for literal in SENSITIVE_LITERALS:
                    self.assertNotIn(literal, content)

    def test_interactive_wrapper_is_documented(self) -> None:
        wrapper = REPO_ROOT / "scripts" / "agent-flow" / "auggie_interactive.sh"
        runbook = (REPO_ROOT / "docs" / "auggie-human-loop-runbook.md").read_text(
            encoding="utf-8"
        )

        self.assertTrue(wrapper.exists())
        self.assertIn("scripts/agent-flow/auggie_interactive.sh", runbook)
        self.assertIn("AUGMENT_SESSION_AUTH", wrapper.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
