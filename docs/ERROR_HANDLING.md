# Error Handling

!!! abstract "Internal Doctrine"
    Error handling in ContentCreaJudge is designed as a team contract:
    business code explains what failed, the API decides how to expose it, and
    the UI consumes one stable error format.

## Purpose

This document defines the internal error-handling architecture used by
ContentCreaJudge.

Its goal is to keep error management:

- explicit for the backend team
- stable for API consumers
- reusable across judges
- easy to extend without mixing business logic and HTTP concerns

This page is an internal implementation guide. It is not a product-facing error
catalog.

## Quick Read By Role

=== "Backend Developer"

    Focus on:

    - typed exceptions in business layers
    - centralized HTTP mapping in `api/error_handlers.py`
    - stable `error.code` values

=== "Judge Author"

    Focus on:

    - defining judge-specific exceptions only when they carry business meaning
    - avoiding raw `ValueError` for known domain cases
    - keeping transport logic out of resolvers and judges

=== "UI Developer"

    Focus on:

    - reading the normalized `error.message`
    - relying on `error.code` for stable branching logic
    - avoiding endpoint-specific assumptions about error shapes

## Why This Architecture Exists

The project must distinguish clearly between:

- a content evaluation result
- an invalid request
- a judge configuration problem
- an unexpected runtime failure

Those are different situations and should not produce the same technical
behavior.

For example:

- unsupported typography locale -> client error
- malformed payload -> transport validation error
- broken YAML configuration -> server-side configuration error
- uncaught runtime crash -> internal server error

Without a shared architecture, these cases quickly degrade into ad hoc
`ValueError`, `HTTPException`, and inconsistent response payloads.

## Main Design Principle

Error handling is split into two distinct responsibilities:

1. Business layers raise application-specific exceptions.
2. The API layer translates those exceptions into normalized HTTP responses.

This separation is intentional.

The business layers should know what went wrong.
The API layer should know how to expose it.

!!! tip "One-sentence rule"
    If the error has business meaning, raise a typed application exception. If
    it has HTTP meaning, map it in the API layer.

## Layer Responsibilities

<div class="grid cards" markdown>

-   __`core`__
    ---
    Shared exception hierarchy and the standard API error envelope.

    Current files:

    - `src/contentcreajudge/core/errors.py`
    - `src/contentcreajudge/core/error_models.py`

-   __Judge Modules__
    ---
    Judge-specific exceptions kept close to the domain they describe.

    Example:

    - `src/contentcreajudge/judges/typography/exceptions.py`

-   __`api`__
    ---
    The only layer responsible for HTTP error mapping and normalized error responses.

    Current file:

    - `src/contentcreajudge/api/error_handlers.py`

</div>

??? info "Detailed responsibilities"
    **`core`**

    - define the base exception hierarchy
    - define stable error codes
    - define the common JSON response envelope

    **Judge modules**

    - express judge-specific failure modes
    - keep domain meaning close to the judge
    - avoid generic `ValueError` or ambiguous exceptions

    **`api`**

    - convert application exceptions into HTTP responses
    - normalize FastAPI and Pydantic validation errors
    - return a stable error payload
    - avoid leaking raw runtime exceptions to clients

## Exception Hierarchy

The base hierarchy is intentionally small.

Current shared classes:

- `ContentCreaJudgeError`
- `DomainError`
- `DomainValidationError`
- `RuleResolutionError`
- `ConfigurationError`
- `InfrastructureError`

Guiding rule:

- use a shared base class for application-specific exceptions
- use specialized subclasses only when they add real business meaning

=== "Shared Base"

    - `ContentCreaJudgeError`
    - `DomainError`
    - `DomainValidationError`
    - `RuleResolutionError`
    - `ConfigurationError`
    - `InfrastructureError`

=== "Judge Specialization Example"

    - `MissingTypographyContextError`
    - `UnsupportedTypographyLocaleError`

## Judge-Specific Exceptions

Judge-specific exceptions are encouraged when the error is meaningful for that
dimension.

Typography currently uses:

- `MissingTypographyContextError`
- `UnsupportedTypographyLocaleError`

This pattern should be reused for other judges when needed:

- `length/exceptions.py`
- `structure/exceptions.py`
- `seo/exceptions.py`

Do not create a judge-specific exception file unless the judge actually needs a
distinct error vocabulary.

## Standard API Error Envelope

The API returns errors using one stable structure:

```json
{
  "error": {
    "code": "unsupported_typography_locale",
    "message": "Unsupported locale for typography evaluation: en-US",
    "details": {
      "locale": "en-US",
      "supported_locales": ["fr-FR"]
    }
  },
  "request_id": null
}
```

This payload exists to make the frontend and tests predictable.

### Field Meaning

- `error.code`: stable machine-readable identifier
- `error.message`: human-readable explanation
- `error.details`: optional structured context
- `request_id`: optional correlation field for future tracing

??? example "How the UI should read this payload"
    In the UI, the preferred display order is:

    1. `error.message`
    2. fallback generic message if absent
    3. optional technical details in a collapsible raw exchange panel

## Mapping Strategy

Current mapping rules:

- `DomainValidationError` -> `422`
- `RuleResolutionError` -> `422`
- FastAPI `RequestValidationError` -> `422`
- `ConfigurationError` -> `500`
- `InfrastructureError` -> `500`
- unexpected `Exception` -> `500`

Principle:

- client-caused invalid input -> `4xx`
- server-side setup/runtime failure -> `5xx`

=== "Client-Oriented Failures"

    - `DomainValidationError` -> `422`
    - `RuleResolutionError` -> `422`
    - `RequestValidationError` -> `422`

=== "Server-Oriented Failures"

    - `ConfigurationError` -> `500`
    - `InfrastructureError` -> `500`
    - unexpected `Exception` -> `500`

## What Should Not Happen

The following patterns should be avoided:

- raising `HTTPException` inside judge or resolver logic
- raising raw `ValueError` for domain-specific cases
- building one-off error JSON directly in endpoint handlers
- returning inconsistent payload shapes across endpoints

These patterns make the codebase harder to reason about and harder to keep
consistent.

!!! warning "Avoid these shortcuts"
    The fastest local fix is often the worst architectural move:

    - `raise HTTPException(...)` inside a judge
    - `raise ValueError(...)` for a recurring business case
    - manual JSON error response built directly in one endpoint
    - endpoint-specific response shape that the UI cannot reuse

## Recommended Development Rules

When implementing new logic:

1. If the problem is business-meaningful, raise a typed application exception.
2. If the problem is specific to one judge, define it near that judge.
3. If the problem is transport-related, let FastAPI validation handle it or map
   it in the API layer.
4. If the problem is unexpected, let the global handler return a safe `500`
   envelope.

## Error Lifecycle

```text
Request
  ->
Transport validation
  ->
Application / resolver / judge
  ->
Typed application exception
  ->
API error handler
  ->
Stable JSON error payload
  ->
UI message + raw exchange
```

## Concrete Example: Typography Locale

=== "Before"

    - the resolver raised `ValueError`
    - the API returned a generic `500`
    - the UI had to infer failure from a vague message

=== "After"

    - the resolver raises `UnsupportedTypographyLocaleError`
    - the API maps it to `422`
    - the response includes a stable `error.code`
    - the UI can display the backend message directly

## Internal Role for the Team

This architecture is not only technical plumbing. It is also a collaboration
contract.

It gives the team a shared rule:

- backend business code raises typed exceptions
- API code translates them
- UI code reads stable error payloads

That alignment reduces ambiguity when several developers work on different
judges in parallel.

!!! note "Why this matters for teamwork"
    A shared doctrine prevents each judge author from inventing a different
    error style. That is especially important when several mini-judges evolve
    in parallel.

## Extension Guidelines

When adding a new judge:

1. Decide whether the judge needs its own exception file.
2. Reuse shared base exceptions whenever possible.
3. Add at least one contract test for the expected API error path.
4. Keep the API error envelope unchanged unless there is a deliberate
   cross-project decision.

When changing the shared error contract:

1. update `core/error_models.py`
2. update `api/error_handlers.py`
3. update the affected tests
4. update this documentation page
