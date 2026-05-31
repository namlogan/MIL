# Codex Worker Runner

`codex_worker` is the first real implementation runner in MIL. It turns an
approved issue/task payload into an isolated Git worktree, a scoped Codex
prompt, required checks, local evidence, and optionally a pushed PR branch.

Before coding, the runner resolves the AI Factory 2.x rule hierarchy from
`.ai-factory/config.yaml` and injects the active sources into the prompt:

```text
.ai-factory/RULES.md
.ai-factory/rules/base.md
.ai-factory/rules/implementation.md
.ai-factory/rules/quality-gates.md
.ai-factory/rules/security.md
.ai-factory/rules/memory.md
.ai-factory/rules/windmill.md
```

Safe defaults:

- `execute_agent=false`
- `push=false`
- `open_pr=false`
- sandbox is `workspace-write`
- approval mode is `never`
- restricted changes block before dispatch

## Inputs

Required task fields:

```json
{
  "task_id": "MIL-123",
  "goal": "Implement a scoped change.",
  "acceptance_criteria": ["Behavior is covered by tests."],
  "allowed_files": ["f/mil/**", "scripts/**", "tests/**"],
  "checks": ["python3 -m unittest discover -s tests -v", "git diff --check"],
  "restricted_changes": []
}
```

Optional context:

- `memory_context`: sanitized Mem0 context pack
- `augment_context`: indexed codebase references from Augment MCP
- `out_of_scope_files`: explicit deny patterns
- `base_branch`: defaults to `main`
- `branch`: defaults to `agent/<task-id>-<slug>`

## Local Dry Run

Use this first. It writes no branch and does not call Codex:

```bash
python3 scripts/agent-flow/codex_worker.py \
  --repo /Users/mac/Documents/MIL \
  --task tests/fixtures/agent_task.json \
  --dry-run \
  --out /tmp/mil-codex-worker.json
```

## Real Local Execution

This creates a Git worktree, runs `codex exec`, runs the task checks, validates
changed files against `allowed_files`, and commits the scoped result locally:

```bash
python3 scripts/agent-flow/codex_worker.py \
  --repo /Users/mac/Documents/MIL \
  --task /path/to/task.json \
  --execute-agent
```

Add `--push --open-pr` only when the branch should be pushed and a PR opened:

```bash
python3 scripts/agent-flow/codex_worker.py \
  --repo /Users/mac/Documents/MIL \
  --task /path/to/task.json \
  --execute-agent \
  --push \
  --open-pr
```

## Windmill Entrypoints

Windmill-safe command pack:

```text
f/mil/codex_worker
```

Shared contract:

```text
f/mil/codex_worker_contract
```

Preview command after a Windmill workspace profile is active:

```bash
wmill script preview f/mil/codex_worker.py \
  -d '{"request":{"task":{"task_id":"MIL-LOCAL","goal":"Prepare a scoped worker run.","acceptance_criteria":["Evidence is produced"],"allowed_files":["docs/**"],"checks":["git diff --check"],"restricted_changes":[]},"options":{"repo_root":"/Users/mac/Documents/MIL"}}}'
```

Windmill should call this before implementation dispatch to produce the exact
prompt, branch, worktree path, evidence path, and `codex exec` command.

## Evidence

Default evidence root:

```text
.ai-factory/qa/codex_worker/<TASK_ID>/
```

Expected files:

- `prompt.md`
- `codex-last-message.md`
- `result.json`

`result.json` records branch, changed files, checks, command outcomes, and final
runner status. It is evidence for the PR and later QA gate, not a merge approval.
