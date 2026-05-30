# Windmill Worker Groups

Use separate worker groups and credentials.

## agent-readonly

Purpose:

- issue intake
- plan validation
- diff review
- QA review

Permissions:

- repository read
- pull request read
- issue/PR comment write, if needed

Must not:

- push branches
- access production secrets
- merge PRs

## agent-write

Purpose:

- scoped implementation
- test generation
- CI fix attempts
- push to `agent/*` or `fix/*`

Permissions:

- repository read/write for non-protected branches
- pull request write

Must not:

- push `main`
- bypass branch protection
- access production secrets
- deploy production

## merge-bot

Purpose:

- enable auto-merge or merge PRs only after required checks pass

Permissions:

- pull request merge through GitHub API

Must not:

- author implementation commits
- override missing checks
- merge restricted changes without human approval

## release

Purpose:

- release notes
- tags
- deployment preparation

Permissions:

- release write
- deployment credentials only after approval

Must require human approval before production deployment.

