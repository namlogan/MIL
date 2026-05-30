# Security Rule

Agents must not print, copy, commit, or request production secrets.

Use least-privilege worker credentials:

- readonly workers may inspect code and comment on PRs
- write workers may push agent branches
- merge workers may merge only after required checks pass
- release workers require human approval before production actions

