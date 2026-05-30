# Auggie Supervised Human Loop Runbook

MIL uses Auggie in a supervised lane while Auggie CLI non-interactive mode is blocked for the account.

## Operating Model

```text
Windmill creates or records the advisory job
Codex opens Auggie interactive TTY
Auggie reviews, diagnoses, or implements only within explicit scope
Codex verifies commands, diff, and evidence
GitHub PR/CI/gate remains the source of truth
Human approves restricted changes and merge decisions
```

This is not unattended automation. It is Codex-operated Auggie work with a visible terminal session and reviewable evidence.

## Start Auggie

From the MIL repo:

```bash
cd /Users/mac/Documents/MIL
scripts/agent-flow/auggie_interactive.sh
```

The wrapper sources `.env.local`, requires `AUGMENT_SESSION_AUTH`, loads `AGENTS.md`, and grants indexing for this workspace.

## Morning Loop

Run this command first:

```text
/command mil-morning-triage
```

For each item Auggie identifies:

```text
/command mil-plan-review issue #<id>
/command mil-pr-review PR #<id>
/command mil-ci-diagnose PR #<id> failing check <name>
/command mil-handoff PR #<id>
```

Codex should then verify Auggie output before posting it to GitHub:

```bash
git status --short --branch
python3 -m unittest discover -s tests -v
git diff --check
```

Use the relevant subset when the task is docs-only or when dependencies are unavailable.

## Allowed Auggie Verdicts

Auggie advisory output must end with one of:

```text
AUGMENT_REVIEW_PASS
AUGMENT_REVIEW_NOTES
AUGMENT_REVIEW_CHANGES_RECOMMENDED
AUGMENT_REVIEW_BLOCKED
```

These are advisory verdicts only. They are not final merge approvals.

## Safety Rules

- Do not paste production secrets into Auggie prompts.
- Do not store Augment session data in tracked files.
- Keep `.env.local` local-only and mode `600`.
- Use Windmill encrypted secrets for deployed workers.
- Auggie is read-only by default.
- Auggie may edit only when the GitHub issue explicitly routes implementation to Auggie.
- Codex must verify Auggie changes before a PR is marked ready.
- Human approval is required for restricted changes, credentials, production deploy behavior, and final merge decisions.

## What Windmill Does

Windmill may:

- create advisory job records
- comment that Auggie review is requested
- store links to transcripts or evidence
- publish labels such as `auggie-review-requested`
- wake Codex/operator workflow

Windmill must not:

- call `auggie --print` while account policy blocks it
- fake an Auggie review without a real Auggie session
- auto-merge based on Auggie output
- store raw Augment credentials in logs or repo files

## Evidence

Use `.ai-factory/qa/auggie_advisory_template.md` for PR comments or local evidence notes.
