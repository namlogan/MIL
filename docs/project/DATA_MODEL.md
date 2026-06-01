# MIL Data Model

## Entities

| Entity | Purpose | Owner | Persistence |
|---|---|---|---|
| GitHub issue | Requirement and scope | Product owner | GitHub |
| GitHub PR | Diff, discussion, checks, merge | Product owner | GitHub |
| Windmill job | Route execution evidence | Windmill | Windmill database |
| Memory record | Sanitized durable lesson | Mem0/local adapter | Mem0 or JSONL |
| Queue item | Local auto-dispatch runtime state | Relay/dispatcher | Ignored local files |

## Relationships

An issue can create one or more plans. A plan dispatches one Codex worker. A
worker creates one PR. A PR receives CI and AI gate statuses before merge.

## Invariants

- Memory records require tenant, repo, provenance, status, visibility, and entity scope.
- Queue files are runtime artifacts and are not source of truth.
- Branch protection, not an agent response, decides mergeability.

## External Data

GitHub webhooks, GitHub status API, Windmill variables, Augment credentials, and
optional Mem0 endpoints are external integration points. Secret values stay out
of Git.

## Migration And Retention

Framework source is retained in Git. Runtime queue/log files are local and
ignored. Memory retention follows the chosen Mem0 or local JSONL policy.
