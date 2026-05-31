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
5. Ask Codex to draft an AI Factory plan using the issue and retrieved context.
6. Write plan artifact under `.ai-factory/plans/`.
7. Comment a concise plan summary on the issue.
8. Request human approval before implementation.

Stop conditions:

- issue fields are missing
- restricted work lacks explicit approval
- plan and acceptance criteria do not match
