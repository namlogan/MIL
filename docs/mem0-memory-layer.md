# MIL Memory0 / Mem0 Layer

Status date: 2026-06-01.

MIL uses Memory0/Mem0 as a controlled SDLC learning layer for agents and
Windmill workflows. It is not source of truth.

```text
Windmill = workflow runner / control-plane
ai-factory = rules, governance, delivery standards
Memory0 / Mem0 = project and agent memory layer
Git + docs + issue + test + audit DB = source of truth
```

## Core Rule

Agents must not call Memory0 directly. All add/search/update/supersede/retire
operations go through the Memory Gateway contract in `f/mil/memory_contract.py`.

The gateway is responsible for:

- schema validation
- secret and raw artifact rejection
- allowlist/denylist enforcement
- required `source_ref`
- metadata and scope enforcement
- operation audit
- optional Mem0 adapter payload generation

## Memory Scopes

Framework memory is reusable across projects:

```json
{
  "scope": "framework",
  "framework_id": "ai-factory-sdlc",
  "status": "approved"
}
```

Project memory is isolated to one project:

```json
{
  "scope": "project",
  "project_id": "mil",
  "repo": "MIL",
  "status": "approved"
}
```

Task/run memory is short-lived and task-scoped:

```json
{
  "scope": "task",
  "project_id": "mil",
  "task_id": "MIL-123",
  "run_id": "windmill-run-123",
  "status": "candidate"
}
```

## Taxonomy

Allowed memory types are intentionally narrow:

```text
framework_rule
security_rule
product_rule
architecture_decision
adr_summary
domain_glossary
requirement_interpretation
implementation_lesson
test_lesson
review_lesson
deployment_runbook
incident_postmortem
agent_handoff
open_question
deprecated_decision
```

Avoid ad hoc types. If a new type feels necessary, update
`.ai-factory/memory/MEMORY_TYPES.yaml`, the schema, tests, and docs together.

## Event Schema

Minimum required fields:

```json
{
  "memory_type": "implementation_lesson",
  "scope": "project",
  "framework_id": "ai-factory-sdlc",
  "project_id": "mil",
  "repo": "MIL",
  "repo_id": "github:namlogan/MIL",
  "task_id": "MIL-123",
  "agent_id": "codex_worker",
  "run_id": "windmill-run-123",
  "status": "candidate",
  "source_ref": "https://github.com/namlogan/MIL/pull/123",
  "source_type": "pull_request",
  "content": "Codex workers must read source docs before writing code.",
  "tags": ["sdlc", "codex"],
  "confidence": "high",
  "sensitivity": "internal",
  "valid_until": "until_superseded",
  "created_by": "memory_gateway"
}
```

No `source_ref` means reject. No project/framework scope means reject.

## Lifecycle

```text
candidate -> reviewed -> approved -> superseded -> retired
```

Only `status=approved` memory may enter a worker context pack. Agents may
propose `candidate` memory in handoff, but they must not mark memory approved.

## Restricted Payloads

The gateway rejects:

- secrets, tokens, API keys, private keys, passwords, `.env` values
- raw customer data
- raw factory image/video
- model weights
- database dumps
- full terminal logs with sensitive data
- raw proprietary source
- unreviewed generated patches
- chain-of-thought
- business or requirement claims without `source_ref`

## Conflict Priority

When memory conflicts with a higher-priority source, memory loses:

```text
1. Compliance / legal / security policy
2. Current PRD / spec / SOP / contract
3. Git code + tests
4. Approved ADR
5. Approved memory
6. Candidate memory
7. Conversation context
```

The correct action is to ignore the memory for the task, create a
`deprecated_decision` conflict event, and route it through
`.windmill/flows/memory_conflict_review.md`.

## Windmill Flow Points

Standard memory flows:

```text
wm_project_bootstrap
wm_memory_preflight
wm_task_context_pack
wm_agent_handoff_collect
wm_pr_merge_memory_writeback
wm_release_memory_pack
wm_incident_digest
wm_memory_conflict_review
wm_memory_maintenance
wm_memory_audit_report
```

The most important operational flows are:

- `wm_memory_preflight`
- `wm_task_context_pack`
- `wm_pr_merge_memory_writeback`
- `wm_memory_maintenance`

## Local Deterministic Adapter

MIL internal memory does not call OpenAI, Ollama, or any external LLM by
default.

```text
mem0_writeback -> Memory Gateway -> local JSONL / optional Mem0 payload
mem0_retrieve  -> approved scoped filters -> context pack -> Codex prompt
```

Local runtime store:

```text
.ai-factory/memory/local_memory.jsonl
```

Audit log:

```text
.ai-factory/memory/audit.jsonl
```

Both are runtime artifacts and ignored by git.

## Optional Mem0 Package Adapter

The OSS `mem0ai` package is optional. Use it only when product/app code or a
future worker explicitly needs Mem0's own extraction/embedding behavior.

Python package check:

```bash
pip install mem0ai
python3 -c 'from mem0 import Memory; print("MEM0_LIBRARY_OK")'
python3 scripts/agent-memory/check_mem0_library.py --runtime python
```

Only this explicit mode needs a configured provider:

```bash
python3 scripts/agent-memory/check_mem0_library.py --runtime python --require-llm
```

## Verification

Run these after changing memory behavior:

```bash
python3 scripts/agent-memory/memory_contract.py --self-test
python3 scripts/agent-memory/check_mem0_provider.py --self-test
python3 scripts/agent-memory/check_mem0_library.py --self-test
python3 scripts/agent-memory/mem0_framework_integration.py --self-test
python3 memory/tools/validate_memory_event.py --schema memory/schemas/memory_event.schema.json --samples memory/samples
python3 memory/tools/scrub_memory_payload.py --check memory/samples/*.json
python3 -m unittest tests.test_memory_contract tests.test_memory0_sdlc_gateway tests.test_mem0_framework_integration -v
```
