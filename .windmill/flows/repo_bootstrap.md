# wm_repo_bootstrap

Purpose: create a repo or module skeleton only after docs and contracts are
ready.

Expected output:
- README and project docs.
- `.ai-factory`, `contracts`, source, tests, tools, deploy, and CI folders.
- Health or smoke test.
- Product CI profile selected or explicitly disabled.

Gate: block skeletons that require production secrets, cloud credentials,
camera, GPU, or binary artifacts in baseline CI unless the project explicitly
requires those dependencies.
