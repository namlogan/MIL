from __future__ import annotations

import importlib.util
import json
import sys
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


class AugmentContextProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = load_module(
            "augment_context_provider",
            "scripts/agent-flow/augment_context_provider.py",
        )

    def test_parse_tool_call_result_builds_context_pack(self) -> None:
        stdout = "\n".join(
            [
                json.dumps({"result": {"protocolVersion": "2024-11-05"}, "id": 1}),
                json.dumps(
                    {
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "The following code sections were retrieved:\nPath: scripts/agent-flow/auto_dispatcher.py",
                                }
                            ]
                        },
                        "jsonrpc": "2.0",
                        "id": 3,
                    }
                ),
            ]
        )

        result = self.provider.parse_tool_call_result(
            stdout,
            response_id=3,
            source_uri="augment://mcp/mil-auggie-local/codebase-retrieval/result",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["context_pack"]), 1)
        self.assertIn("auto_dispatcher.py", result["context_pack"][0]["summary"])
        self.assertEqual(
            result["context_pack"][0]["source_uri"],
            "augment://mcp/mil-auggie-local/codebase-retrieval/result",
        )

    def test_parse_tool_call_result_redacts_secret_shapes(self) -> None:
        stdout = json.dumps(
            {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "accessToken: 13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318",
                        }
                    ]
                },
                "id": 3,
            }
        )

        result = self.provider.parse_tool_call_result(
            stdout,
            response_id=3,
            source_uri="augment://mcp/mil-auggie-local/codebase-retrieval/result",
        )
        serialized = json.dumps(result)

        self.assertNotIn("13f6f4f5c84c0ce8ec2b780595dcb28ca2019c2f36f313ac8146497702999318", serialized)
        self.assertIn("[REDACTED_TOKEN]", serialized)


if __name__ == "__main__":
    unittest.main()
