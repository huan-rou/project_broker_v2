# Contributing

This repository is currently optimized for fast thin-slice implementation.

Rules:

- Keep the Docker path working.
- Add migrations for schema changes.
- Do not add fake OCR/LLM fallbacks unless the provider policy changes.
- Keep all job failures structured with `code`, `stage`, `retryable`, and `next_action`.
