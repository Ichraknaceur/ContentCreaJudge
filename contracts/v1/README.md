# Contracts V1

This directory groups all V1 contract artifacts for ContentCreaEvaluator.

## Scope

V1 covers a synchronous rule-based evaluation contract for editorial content.

## Subdirectories

- `request/`: request contract assets for `/v1/evaluations`
- `response/`: response contract assets for `/v1/evaluations`
- `shared/`: reusable field and status references
- `examples/`: V1 example payloads

## Guidance

- keep artifacts aligned with `docs/API_CONTRACT.md`
- prefer additive evolution within V1
- reserve breaking changes for a future version directory
