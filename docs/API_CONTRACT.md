# API Contract

## Purpose

This document defines the V1 API contract for ContentCreaEvaluator at a
functional level. It does not prescribe implementation details or framework
choices. Its goal is to keep request and response semantics stable and
understandable for backend developers, client developers, and future
integrations.

## Contract Scope

V1 covers a synchronous evaluation API for rule-based editorial validation.

The contract supports:

- content submission for evaluation
- profile-based rule resolution
- explainable evaluation results
- per-dimension reporting
- stable top-level status and score semantics

The contract does not yet support:

- content correction
- rewrite suggestions
- asynchronous jobs
- bulk processing
- semantic scoring
- model-generated rationale

## API Style

- Request-response, synchronous
- JSON payloads
- Versioned contract
- Explainable output by default

## Versioning Strategy

Use explicit API versioning from V1 onward.

Recommended approach:

- API path versioning such as `/v1/...`
- rule profile versioning inside the response metadata
- backward-incompatible response changes only in a new API version

This separates:

- transport contract version
- business rule profile version

Those versions should not be treated as the same thing.

## Primary Endpoint

### `POST /v1/evaluations`

Creates a single evaluation from one content payload.

## Current Exposed Endpoints

The current repository foundation exposes these routes:

- `GET /`
- `GET /health`
- `POST /api/v1/evaluations`

The versioned business endpoint currently implemented in the codebase uses the
path `/api/v1/evaluations`.

### Request Purpose

The client sends editorial content plus the minimum metadata needed to evaluate
it against structural and formal rules.

### Response Purpose

The service returns:

- the overall evaluation decision
- a global score
- per-dimension outcomes
- findings with evidence and rule references

## Request Contract

### Conceptual Request Shape

An evaluation request should contain these logical sections:

- request metadata
- content payload
- evaluation configuration
- optional client context

### Required Fields

- `content`
  - the editorial content to evaluate
- `profile`
  - the rule profile to apply

### Optional Fields

- `content_title`
- `content_type`
- `channel`
- `locale`
- `target_keywords`
- `declared_sources`
- `request_id`
- `client_context`

### Field Roles

#### `content`

- The main text body evaluated by the service.
- This is the only mandatory business payload for the actual content.

#### `profile`

- Selects the rule set and aggregation policy.
- Examples may later include profiles by brand, channel, or publication type.

#### `content_title`

- Optional title or headline.
- Useful for structure and SEO-related rules.

#### `content_type`

- Optional classification such as article, landing page, or newsletter.
- Can influence which rules apply.

#### `channel`

- Optional publication channel such as blog, website, or email.
- Supports future rule specialization.

#### `locale`

- Optional locale for typography and language-specific checks.

#### `target_keywords`

- Optional keyword list for basic SEO presence validation in V1.

#### `declared_sources`

- Optional source references explicitly supplied by the client.
- Can complement sources extracted from content.

#### `request_id`

- Optional client-generated identifier for traceability.

#### `client_context`

- Optional client metadata for debugging or downstream correlation.
- Should not drive evaluation semantics directly in V1 unless explicitly modeled
  as profile selection input.

## Example Request Semantics

The request represents one editorial unit to evaluate.

A single request should not contain:

- multiple unrelated articles
- a batch of documents
- correction instructions
- user preference feedback

Those belong to future workflows, not the V1 evaluation contract.

## Response Contract

### Conceptual Response Shape

The response should contain these logical sections:

- request trace metadata
- overall evaluation outcome
- per-dimension results
- findings
- rule profile metadata

### Top-Level Fields

- `evaluation_id`
- `status`
- `score`
- `summary`
- `dimension_results`
- `blocking_issues`
- `metadata`

### Field Roles

#### `evaluation_id`

- Server-generated identifier for the evaluation run.

#### `status`

- Top-level decision for the evaluated content.

Recommended V1 statuses:

- `pass`
- `warn`
- `fail`
- `error`

Guidance:

- `fail` means the content was evaluated and did not meet required rules.
- `error` means the service could not complete evaluation reliably.

#### `score`

- Numeric aggregate signal for the evaluated content.
- Should remain separate from the top-level decision.

#### `summary`

- Human-readable short summary of the main outcome.
- Should remain concise and explainable.

#### `dimension_results`

- Collection of per-dimension results.
- One result per enabled mini-judge.

#### `blocking_issues`

- Subset of findings that triggered automatic top-level failure.

#### `metadata`

- Carries traceable evaluation metadata, such as:
  - API version
  - rule profile
  - rule profile version
  - evaluation timestamp
  - optional request correlation identifiers

## Current Placeholder Response

At the current implementation stage, `POST /api/v1/evaluations` returns a
placeholder acceptance response instead of a full evaluation result.

Its current logical fields are:

- `status`
- `message`
- `received_profile`
- `request_id`
- `next_step`

This is intentionally temporary. It exists to stabilize the integration between
the FastAPI transport layer and the Streamlit UI before the real evaluation
pipeline is wired.

Recommended interpretation:

- `status="accepted"` means the payload shape was accepted by the API
- it does not yet mean the content has been evaluated

## Per-Dimension Result Contract

Each element in `dimension_results` should describe one evaluation dimension.

### Required Logical Fields

- `dimension`
- `status`
- `score`
- `findings`
- `applied_rules`

### Recommended Statuses

- `pass`
- `warn`
- `fail`
- `not_applicable`
- `unknown`

### Meaning

- `pass`: dimension satisfied applicable rules
- `warn`: dimension has issues but no blocker-level failure
- `fail`: dimension violated significant or blocking rules
- `not_applicable`: dimension is irrelevant for this request
- `unknown`: dimension could not be fully evaluated reliably

## Finding Contract

Each finding should be structured and explainable.

### Required Logical Fields

- `rule_id`
- `severity`
- `message`
- `evidence`

### Optional Logical Fields

- `criticality`
- `location`
- `suggested_action`

### Field Roles

#### `rule_id`

- Stable identifier of the rule that produced the finding.

#### `severity`

- Indicates the importance of the issue inside the dimension result.

#### `message`

- Human-readable explanation of what was detected.

#### `evidence`

- Minimal supporting detail that makes the finding auditable.
- For example:
  - missing heading structure
  - word count under threshold
  - missing target keyword
  - outdated time reference
  - missing source URL

#### `criticality`

- Indicates whether the rule is blocking, major, or minor from the policy point
  of view.

#### `location`

- Optional pointer to where the issue was detected in the content.

#### `suggested_action`

- Reserved for future expansion.
- In V1, this field may be omitted entirely because correction is outside scope.

## Error Contract

Errors should distinguish invalid requests from service failures.

### Validation Errors

Use when the request shape or mandatory fields are invalid.

Recommended contents:

- stable error code
- short message
- optional field-level details

### Evaluation Errors

Use when the system cannot evaluate reliably because of internal or dependency
issues.

Recommended contents:

- stable error code
- short message
- correlation identifier

Do not expose internal stack traces or implementation details in the public
contract.

## Health Contract

The health endpoint currently returns a minimal service payload with:

- `status`
- `service`
- `version`

This endpoint is intended for:

- local verification
- UI connectivity checks
- future operational monitoring

## Contract Design Rules

### 1. Keep Response Semantics Stable

- Avoid renaming top-level fields casually.
- Prefer additive changes over breaking changes.

### 2. Always Return Explainable Results

- A result without rule references is not sufficient.
- Every non-pass outcome should be traceable.

### 3. Keep Request Minimal

- Only ask clients for fields the evaluator genuinely needs.
- Do not overload the request with future concerns.

### 4. Separate Policy from Transport

- The API contract should stay stable even if rule thresholds evolve.
- Policy evolution belongs to rule profiles, not to transport redesign.

## V1 Contract Boundaries

What belongs in V1:

- one evaluation per request
- synchronous processing
- deterministic result structure
- per-dimension reporting
- explicit rule findings

What should come later:

- correction payloads
- suggested rewrites
- semantic analysis traces
- batch identifiers and asynchronous job states
- confidence scores from learned systems

## Relation to the `contracts/` Directory

The `docs/` contract document explains semantics for humans.

The `contracts/` directory should hold versioned contract artifacts for the
repository, such as:

- request references
- response references
- shared field definitions
- examples

That separation keeps:

- `docs/` readable for developers and stakeholders
- `contracts/` organized for contract assets and future machine-readable schemas

## Summary

The V1 API contract should remain:

- explicit
- versioned
- minimal
- explainable
- stable under future rule evolution

That gives the project a clean foundation before adding richer semantics or more
advanced evaluation modes.
