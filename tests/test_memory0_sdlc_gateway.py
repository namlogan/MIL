from __future__ import annotations

import importlib.util
import json
import subprocess
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


memory_contract = load_module("memory0_sdlc_contract", "f/mil/memory_contract.py")


def event_metadata(**overrides: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "tenant_id": "org_mil",
        "workspace_id": "engineering",
        "repo": "MIL",
        "repo_id": "github:namlogan/MIL",
        "project_id": "mil",
        "framework_id": "ai-factory-sdlc",
        "user_id": "repo:github:namlogan/MIL",
        "agent_id": "codex_worker",
        "run_id": "windmill-run-123",
        "source_ref": "https://github.com/namlogan/MIL/pull/50",
        "source_type": "pull_request",
        "confidence": "high",
        "scope": "project",
        "status": "candidate",
        "sensitivity": "internal",
        "created_by": "memory_gateway",
    }
    metadata.update(overrides)
    return metadata


class Memory0SdlcGatewayTests(unittest.TestCase):
    def test_writeback_creates_candidate_and_requires_approval_for_prompt_context(self) -> None:
        record = memory_contract.build_memory_record(
            project="MIL",
            task_id="MEM-101",
            memory_type="implementation_lesson",
            text="Codex workers must read source docs before writing code.",
            metadata=event_metadata(),
        )

        self.assertEqual(record["status"], "candidate")
        self.assertEqual(record["content"], record["memory"])
        self.assertEqual(record["source_ref"], "https://github.com/namlogan/MIL/pull/50")

        with tempfile.TemporaryDirectory() as tmpdir:
            store = memory_contract.LocalJsonlMemoryStore(Path(tmpdir) / "memory.jsonl")
            store.add(record)
            approved = dict(record)
            approved["memory_id"] = "mem-approved"
            approved["status"] = "approved"
            approved["metadata"] = dict(approved["metadata"], status="approved", approved_by="logan")
            store.add(approved)

            filters = memory_contract.build_search_filters(
                tenant_id="org_mil",
                repo_id="github:namlogan/MIL",
                project_id="mil",
                memory_types=["implementation_lesson"],
                user_id="repo:github:namlogan/MIL",
            )
            results = store.search("source docs", filters=filters)

        self.assertEqual([result["memory_id"] for result in results], ["mem-approved"])

    def test_gateway_rejects_missing_source_ref_and_sensitive_payloads(self) -> None:
        missing_source = event_metadata()
        missing_source.pop("source_ref")
        with self.assertRaisesRegex(ValueError, "source_ref is required"):
            memory_contract.build_memory_record(
                project="MIL",
                task_id="MEM-102",
                memory_type="implementation_lesson",
                text="A reusable lesson.",
                metadata=missing_source,
            )

        with self.assertRaisesRegex(ValueError, "restricted memory payload"):
            memory_contract.build_memory_record(
                project="MIL",
                task_id="MEM-102",
                memory_type="implementation_lesson",
                text="OPENAI_API_KEY=sk-123456789012345678901234567890",
                metadata=event_metadata(),
            )

    def test_lifecycle_update_audits_review_approve_supersede_and_retire(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "memory.jsonl"
            audit_path = Path(tmpdir) / "audit.jsonl"
            store = memory_contract.LocalJsonlMemoryStore(store_path)
            record = store.add(
                memory_contract.build_memory_record(
                    project="MIL",
                    task_id="MEM-103",
                    memory_type="test_lesson",
                    text="Run memory gateway contract tests before changing flows.",
                    metadata=event_metadata(source_ref="https://github.com/namlogan/MIL/pull/51"),
                ),
                audit_path=audit_path,
            )

            reviewed = store.update_status(
                record["memory_id"],
                "reviewed",
                source_ref="https://github.com/namlogan/MIL/pull/51#discussion_r1",
                actor="codex_qa",
                audit_path=audit_path,
            )
            approved = store.update_status(
                record["memory_id"],
                "approved",
                source_ref="https://github.com/namlogan/MIL/pull/51",
                actor="logan",
                audit_path=audit_path,
            )
            superseded = store.update_status(
                record["memory_id"],
                "superseded",
                source_ref="docs/project/TEST_STRATEGY.md",
                actor="memory_maintenance",
                audit_path=audit_path,
            )
            retired = store.update_status(
                record["memory_id"],
                "retired",
                source_ref="windmill-run-456",
                actor="memory_maintenance",
                audit_path=audit_path,
            )

            audit_actions = [
                json.loads(line)["action"]
                for line in audit_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(reviewed["status"], "reviewed")
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(superseded["status"], "superseded")
        self.assertEqual(retired["status"], "retired")
        self.assertEqual(audit_actions, ["add", "update", "update", "supersede", "retire"])

    def test_conflict_event_prefers_source_of_truth_over_memory(self) -> None:
        record = memory_contract.build_memory_record(
            project="MIL",
            task_id="MEM-104",
            memory_type="architecture_decision",
            text="Use memory as source of truth.",
            metadata=event_metadata(status="approved", approved_by="logan"),
            approved=True,
        )

        conflict = memory_contract.build_memory_conflict_event(
            record,
            source_ref="docs/project/PRD.md",
            reason="Current PRD says Git/docs/issues/tests are source of truth.",
        )

        self.assertEqual(conflict["memory_type"], "deprecated_decision")
        self.assertEqual(conflict["status"], "candidate")
        self.assertEqual(conflict["conflict_policy"][0], "compliance_legal_security")
        self.assertIn("docs/project/PRD.md", conflict["content"])

    def test_schema_samples_and_tools_match_repository_contract(self) -> None:
        required_paths = [
            ".ai-factory/memory/MEMORY_POLICY.md",
            ".ai-factory/memory/MEMORY_TYPES.yaml",
            ".ai-factory/memory/CONTEXT_PACK_TEMPLATE.md",
            ".ai-factory/memory/HANDOFF_MEMORY_TEMPLATE.md",
            "memory/schemas/memory_event.schema.json",
            "memory/samples/architecture_decision.sample.json",
            "memory/samples/implementation_lesson.sample.json",
            "memory/tools/validate_memory_event.py",
            "memory/tools/scrub_memory_payload.py",
            ".windmill/flows/memory_preflight.md",
            ".windmill/flows/task_context_pack.md",
            ".windmill/flows/pr_merge_writeback.md",
            ".windmill/flows/memory_maintenance.md",
            ".windmill/flows/incident_digest.md",
            ".windmill/flows/memory_conflict_review.md",
            ".windmill/flows/memory_audit_report.md",
            "apps/memory_gateway/app/main.py",
            "apps/memory_gateway/app/policy.py",
            "apps/memory_gateway/app/scrubber.py",
            "apps/memory_gateway/app/schemas.py",
            "apps/memory_gateway/app/mem0_client.py",
            "apps/memory_gateway/app/audit.py",
        ]
        for relative_path in required_paths:
            with self.subTest(path=relative_path):
                self.assertTrue((REPO_ROOT / relative_path).exists())

        completed = subprocess.run(
            [
                sys.executable,
                "memory/tools/validate_memory_event.py",
                "--schema",
                "memory/schemas/memory_event.schema.json",
                "--samples",
                "memory/samples",
            ],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

        completed = subprocess.run(
            [
                sys.executable,
                "memory/tools/scrub_memory_payload.py",
                "--check",
                "memory/samples/architecture_decision.sample.json",
                "memory/samples/implementation_lesson.sample.json",
            ],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

        rules = (REPO_ROOT / ".ai-factory" / "RULES.md").read_text(encoding="utf-8")
        memory_rules = (REPO_ROOT / ".ai-factory" / "rules" / "memory.md").read_text(
            encoding="utf-8"
        )
        memory_policy = (
            REPO_ROOT / ".ai-factory" / "memory" / "MEMORY_POLICY.md"
        ).read_text(encoding="utf-8")
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## Memory Policy", rules)
        self.assertIn("Read approved memory before task planning", rules)
        self.assertIn("Back up local JSONL runtime memory separately", rules)
        self.assertIn("back up `.ai-factory/memory/*.jsonl`", memory_rules)
        self.assertIn("## Runtime Backup", memory_policy)
        self.assertIn("Restore local memory only into the same", memory_policy)
        self.assertIn("## Memory Preflight", agents)
        self.assertIn("## Memory Candidate After Task", agents)


if __name__ == "__main__":
    unittest.main()
