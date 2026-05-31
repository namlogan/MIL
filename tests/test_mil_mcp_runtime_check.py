from __future__ import annotations

import importlib.util
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


class MilMcpRuntimeCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = load_module(
            "check_mil_mcp_runtime",
            "scripts/agent-flow/check_mil_mcp_runtime.py",
        )

    def test_parse_codex_mcp_list_requires_mil_server(self) -> None:
        output = f"""
Name              Command                                                           Args  Env  Cwd  Status   Auth
mil-auggie-local  {REPO_ROOT / "scripts" / "agent-flow" / "auggie_mcp_server.sh"}  -     -    -    enabled  Unsupported
"""

        result = self.checker.parse_codex_mcp_list(
            output=output,
            repo_root=REPO_ROOT,
        )

        self.assertEqual(result["server_present"], True)
        self.assertEqual(result["server_enabled"], True)
        self.assertEqual(result["command_matches_repo"], True)

    def test_parse_codex_mcp_list_rejects_flange_scoped_server(self) -> None:
        output = """
Name              Command                                                            Args  Env  Cwd  Status   Auth
mil-auggie-local  /Users/mac/Desktop/FLANGE/scripts/agent-flow/auggie_mcp_server.sh  -     -    -    enabled  Unsupported
"""

        result = self.checker.parse_codex_mcp_list(
            output=output,
            repo_root=REPO_ROOT,
        )

        self.assertEqual(result["server_present"], True)
        self.assertEqual(result["server_enabled"], True)
        self.assertEqual(result["command_matches_repo"], False)

    def test_parse_mcp_smoke_requires_codebase_retrieval_and_mil_index(self) -> None:
        stdout = """
{"result":{"tools":[{"name":"codebase-retrieval"}]},"jsonrpc":"2.0","id":2}
"""
        stderr = f"Workspace indexing complete: {REPO_ROOT}"

        result = self.checker.parse_mcp_smoke(
            stdout=stdout,
            stderr=stderr,
            repo_root=REPO_ROOT,
        )

        self.assertTrue(result["tool_available"])
        self.assertTrue(result["mil_workspace_indexed"])
        self.assertTrue(result["ok"])

    def test_parse_mcp_smoke_rejects_wrong_workspace_index(self) -> None:
        stdout = """
{"result":{"tools":[{"name":"codebase-retrieval"}]},"jsonrpc":"2.0","id":2}
"""
        stderr = "Workspace indexing complete: /Users/mac/Desktop/FLANGE"

        result = self.checker.parse_mcp_smoke(
            stdout=stdout,
            stderr=stderr,
            repo_root=REPO_ROOT,
        )

        self.assertTrue(result["tool_available"])
        self.assertFalse(result["mil_workspace_indexed"])
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
