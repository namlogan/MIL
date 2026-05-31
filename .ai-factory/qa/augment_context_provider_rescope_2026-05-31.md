# Augment Context Provider Rescope Evidence

Date: 2026-05-31
Issue: https://github.com/namlogan/MIL/issues/3

## Decision

MIL will not use Auggie as a coding worker.

Codex remains the only coding worker for:

```text
create_branch
implement
test
open_pr
fix_ci
write_pr_evidence
```

Augment/Auggie is limited to:

```text
expose_codebase_index
retrieve_code_context
summarize_symbols
answer_codebase_context_questions
provide_codebase_context
supervised advisory notes when explicitly requested
```

## Reason

The account still blocks Auggie CLI non-interactive mode, and unattended Auggie coding is not needed for the MIL control plane. The safer design is to let Codex own code changes while Augment provides indexed codebase context to Codex sessions.

## Contract Changes

- `.ai-factory/runtime/agents.json` now defines `augment_context_provider`.
- `.ai-factory/runtime/agents.json` no longer defines `auggie_supervised_developer`.
- `scripts/agent-flow/mil_flow.py` and `f/mil/flow_contract.py` reject non-Codex developer agents.
- Flow calls now use `augment_context` before Codex planning, review, QA, and CI-fix work.
- `coding_agent_dispatch` documents Codex as the only supported coding lane.

## Remaining Work

Validate the active Codex client can call the Augment MCP context provider in the intended runtime environment. This is separate from Auggie CLI non-interactive mode.
