# Developer Guide

## Purpose

This guide is for developers working on ContentCreaEvaluator internally. It
explains how the service should be organized, where new logic belongs, and which
design decisions should remain stable as the codebase grows.

This is not an API usage guide. It is an internal guide for building and
maintaining the backend cleanly.

The repository currently contains both:

- a FastAPI backend foundation
- a Streamlit UI used as a client-facing demo surface

## Working Model

Think about the service as a pipeline:

```text
Request -> Validation -> Rule Resolution -> Preprocessing -> Judges
-> Aggregation -> Response
```

For the current scaffold, there is also a shorter operational loop:

```text
Streamlit UI -> FastAPI API -> Placeholder evaluation response
```

The main rule for contributors is simple:

- do not let one stage absorb responsibilities from another stage

That discipline matters more than any specific file layout.

## Package Boundaries

### `api`

- Put only transport concerns here.
- Good examples:
  - request parsing
  - schema validation
  - response serialization
  - HTTP error mapping
- Avoid:
  - rule evaluation logic
  - scoring logic
  - text parsing

### `application`

- Put orchestration here.
- This layer coordinates the use case.
- It should know the workflow, but not the internal implementation details of
  every judge.

### `domain`

- Put shared business semantics here.
- This includes:
  - statuses
  - dimensions
  - severity levels
  - rule criticality
  - conceptual evaluation objects
- Keep this layer framework-agnostic.

### `rules`

- Put rule profiles and evaluation policy here.
- Rule definition should be data-driven as much as possible.
- Avoid scattering thresholds directly inside judge logic when those thresholds
  are profile policy rather than judge mechanics.

### `preprocessing`

- Put reusable content analysis here.
- Anything that multiple judges need should be extracted once in preprocessing.
- Typical examples:
  - heading extraction
  - paragraph segmentation
  - word counts
  - link extraction
  - keyword occurrence detection

### `judges`

- Each judge evaluates one dimension only.
- A judge should not:
  - call another judge
  - decide the global result
  - parse raw input from scratch if preprocessing already provides the data

### `aggregation`

- Only aggregation decides the top-level result.
- Keep all weighting and blocker logic here, not inside judges.

### `adapters`

- Infrastructure-specific integrations belong here.
- In V1, the main example is source validation support.
- Core evaluation logic should be able to run without knowing adapter details.

### `ui`

- Put demo-facing presentation logic here.
- Good examples:
  - backend status display
  - evaluation form composition
  - response rendering
  - client demo progress views
- Avoid:
  - evaluation business rules
  - scoring logic
  - request semantics that contradict the API contract

## Internal Conventions

### 1. Keep the Domain Language Stable

Prefer a small, explicit vocabulary that everyone uses consistently:

- evaluation
- dimension
- rule
- finding
- evidence
- severity
- criticality
- score
- status

Avoid introducing overlapping synonyms for the same concept.

### 2. Make Judges Boring

The best judge is easy to understand.

- One concern
- One input contract
- One output contract
- Deterministic behavior
- Minimal hidden state

If a judge starts becoming large, split its internal checks into smaller rule
evaluation steps, but keep one public judge responsibility.

### 3. Preprocess Once, Reuse Everywhere

If two judges need the same derived fact, extract it in preprocessing.

Benefits:

- consistent interpretation across judges
- less duplicate logic
- easier testing
- simpler debugging

### 4. Prefer Explicit Rule IDs

Every finding should map to a stable rule identifier.

Why this matters:

- responses stay explainable
- tests stay readable
- future analytics become possible
- versioned rule profiles become easier to manage

### 5. Separate Decision from Score

Do not collapse everything into one number.

- score expresses weighted quality or compliance level
- decision expresses whether the content passed the required bar

A blocking failure should remain visible even if the weighted score looks strong.

## How to Add a New Judge

When adding a new evaluation dimension later, follow this sequence:

1. Define the business need and scope of the dimension.
2. Decide whether the needed facts belong in preprocessing.
3. Add or update the rule profile configuration for that dimension.
4. Implement the new judge under `judges/`.
5. Register it in the judge orchestrator.
6. Extend aggregation only if the new dimension changes weighting policy.
7. Add unit and integration tests.
8. Update architecture and API documentation if the response shape changes.

Before adding a judge, check whether the behavior is truly a new dimension or
just another rule inside an existing dimension.

## How to Decide Where Logic Belongs

Use these rules during development:

- If it extracts reusable facts from raw content, it belongs in preprocessing.
- If it interprets one dimension against its rules, it belongs in a judge.
- If it decides global pass or fail or computes the overall score, it belongs in
  aggregation.
- If it handles transport or serialization, it belongs in `api`.
- If it calls an external system or network dependency, it belongs in an
  adapter.

## Testing Strategy

Testing should mirror the architecture.

### Unit Tests

- preprocessing tests validate extracted facts
- judge tests validate rule interpretation per dimension
- aggregation tests validate blocker and weighting behavior

### Integration Tests

- application-level tests validate the full evaluation flow
- adapter integration tests validate source-check behavior and failure modes

### Contract Tests

- API contract tests validate request and response stability

### UI Verification

- keep UI logic lightweight and mostly presentation-oriented
- verify that the UI still targets the correct backend endpoints
- prefer keeping business assertions in API tests rather than UI tests

## Failure Handling Guidelines

Not every issue should crash the whole evaluation.

Recommended approach:

- validation errors: reject the request early
- judge-level rule failures: return structured findings
- adapter uncertainty: represent as `unknown` when appropriate
- unexpected system errors: surface a clear service error without leaking internals

The important distinction is:

- content failed the rules
- the service could not evaluate reliably

Those are not the same problem and should not share the same status.

## Observability Expectations

Even in V1, keep operational visibility in mind.

Track at least:

- request count
- evaluation duration
- failure count
- judge-level execution outcomes
- adapter errors

Logs should help answer:

- what was evaluated
- which profile was used
- which dimensions failed
- whether the issue was business-related or technical

## Documentation Expectations

When changing the architecture or evaluation semantics, update documentation in
the same change set.

At minimum:

- update the architecture doc when package boundaries or flow change
- update the developer guide when internal conventions change
- update API docs when request or response contracts change
- update contributing guidance if the development workflow changes

When changing the demo surface:

- update the docs README if local run commands change
- update architecture docs if the UI layer or integration flow changes
- document any new environment variables used by the UI

## Local Run Commands

The current local workflow is:

- `make run` to start the FastAPI backend
- `make run-ui` to start the Streamlit UI
- `make lint` for Ruff
- `make typecheck` for Ty
- `make test` for pytest

## V1 Guardrails

To keep the service clean and production-ready, contributors should resist these
temptations in V1:

- do not introduce ML dependencies
- do not add a recommendation engine
- do not persist evaluation history unless there is a clear product requirement
- do not distribute judges across processes or services
- do not over-model every rule as a separate subsystem

The V1 design wins by being predictable, explicit, and easy to reason about.

## Suggested Documentation Set

The backend should eventually maintain these living documents:

- architecture overview
- developer guide
- API contract reference
- rule profile reference
- operational runbook

For now, the first two are enough to create a stable foundation.
