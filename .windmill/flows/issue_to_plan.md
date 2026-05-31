# Windmill Flow: issue_to_plan

Trigger:

```text
GitHub issue label: agent:plan
manual Windmill form: repo + issue number
```

Steps:

1. Fetch issue title, body, labels, and comments.
2. Validate required issue fields.
3. Checkout the base branch in a clean workspace.
4. Request Augment codebase context for the issue scope.
5. Retrieve scoped mem0 project/task memory relevant to the issue.
6. Ask Codex to draft an AI Factory plan using the issue, retrieved code context, and sanitized memory.
7. Store a sanitized plan summary in project memory.
8. Write plan artifact under `.ai-factory/plans/`.
9. Comment a concise plan summary on the issue.
10. Request human approval before implementation.

Stop conditions:

- issue fields are missing
- restricted work lacks explicit approval
- plan and acceptance criteria do not match
- memory provider attempts to store secrets or raw transcripts
