# Worker Service Template

Baseline for background jobs, queues, and scheduled work.

Include:
- Job contract and retry policy.
- Idempotency key or duplicate protection.
- Dead-letter handling.
- Structured logs and metrics.
- Unit tests for retry, failure, and cancellation paths.
- Smoke command for local execution.

Worker tasks that mutate data must include rollback or repair guidance.
