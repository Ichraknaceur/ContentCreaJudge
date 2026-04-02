# Architecture

## Purpose

ContentCreaEvaluator is a Python backend service that evaluates editorial
content against structural and formal rules. V1 is intentionally rule-based and
deterministic. It does not rewrite content, infer author intent, or use machine
learning.

The architecture should stay simple enough for a small team to maintain, while
leaving clear extension points for future semantic analysis and recommendation
layers.

## V1 Scope

The system evaluates the following dimensions:

- Structure
- Length
- Typography
- Evergreen compliance
- CTA compliance
- Sources validation
- Basic SEO keyword presence

## High-Level Architecture

```text
Client
  |
  +--> Streamlit UI
  |       |
  |       v
  |   FastAPI Endpoints
  |
  v
API / Transport Layer
  |
  v
Evaluation Application Service
  |
  +--> Rule Profile Resolver
  |
  +--> Preprocessing Pipeline
  |       |
  |       v
  |   PreprocessedContent
  |
  +--> Judge Orchestrator
          |
          +--> Structure Judge
          +--> Length Judge
          +--> Typography Judge
          +--> Evergreen Judge
          +--> CTA Judge
          +--> Sources Judge
          +--> SEO Keyword Judge
  |
  v
Aggregation Layer
  |
  v
Response Builder
  |
  v
EvaluationResponse
```

## Current Implemented Foundation

The repository currently includes the following working foundation pieces:

- FastAPI application bootstrap
- root discovery endpoint: `GET /`
- health endpoint: `GET /health`
- evaluation intake placeholder: `POST /api/v1/evaluations`
- Streamlit UI for local demos and manual request submission

These are scaffolding elements, not the full evaluator yet. The preprocessing,
judge execution, and aggregation layers are still architectural targets rather
than fully implemented workflow stages.

## Main Components

### API / Transport Layer

- Responsibility: expose the service to external clients.
- Handles:
  - request validation at transport level
  - input format normalization
  - error mapping
  - response serialization
- Does not contain business evaluation logic.

### Evaluation Application Service

- Responsibility: orchestrate the full evaluation workflow.
- Acts as the entry point for the evaluation use case.
- Coordinates preprocessing, judge execution, aggregation, and response
  construction.

### Rule Profile Resolver

- Responsibility: load the applicable rule profile for a request.
- Defines:
  - enabled judges
  - thresholds
  - weights
  - criticality levels
- Keeps rule policy separate from judge mechanics.

### Preprocessing Pipeline

- Responsibility: convert raw content into reusable derived facts.
- Avoids duplicated parsing logic inside judges.
- Produces a shared `PreprocessedContent` object.

### Judge Orchestrator

- Responsibility: execute all enabled mini-judges in a consistent way.
- Ensures each judge receives:
  - the same canonical preprocessed content
  - the rule subset relevant to that dimension
- Collects judge outputs without embedding aggregation rules.

### Aggregation Layer

- Responsibility: combine all judge outputs into a single decision.
- Applies rule criticality and weighting.
- Produces the overall score, status, and summary findings.

### Response Builder

- Responsibility: produce a stable, explainable API response.
- Translates internal results into a client-facing contract.

## Proposed Package Structure

The project package can remain rooted under `src/contentcreajudge/`, with the
service name exposed externally as ContentCreaEvaluator.

```text
src/contentcreajudge/
  api/
  application/
  domain/
  rules/
  preprocessing/
  ui/
  judges/
    structure/
    length/
    typography/
    evergreen/
    cta/
    sources/
    seo/
  aggregation/
  adapters/
    sources/
  observability/
```

## Module Breakdown

### `api`

- Responsibility:
  - accept requests
  - validate external payloads
  - map domain outcomes to API responses
- Inputs:
  - raw HTTP or service request payload
- Outputs:
  - `EvaluationRequest` into the application layer
  - serialized `EvaluationResponse` back to the caller

Current concrete endpoints:

- `GET /`
- `GET /health`
- `POST /api/v1/evaluations`

### `application`

- Responsibility:
  - orchestrate the end-to-end evaluation use case
  - coordinate all domain services
- Inputs:
  - validated `EvaluationRequest`
- Outputs:
  - completed evaluation result ready for response building

### `domain`

- Responsibility:
  - hold the core business vocabulary
  - define statuses, severities, dimensions, rule criticality, and evaluation
    semantics
- Inputs:
  - validated content and rule definitions
- Outputs:
  - canonical concepts shared by all layers

### `rules`

- Responsibility:
  - define rule profiles and evaluation policy
  - keep thresholds and weights configurable
- Inputs:
  - profile identifier, content type, channel, locale, or other request metadata
- Outputs:
  - rule sets and aggregation policy for one evaluation run

### `preprocessing`

- Responsibility:
  - normalize text
  - extract structure and reusable facts
  - prepare canonical evidence for judges
- Inputs:
  - raw content plus request metadata
- Outputs:
  - `PreprocessedContent`

### `judges`

- Responsibility:
  - evaluate a single dimension each
  - return focused, explainable results
- Inputs:
  - `PreprocessedContent`
  - dimension-specific rules
- Outputs:
  - `JudgeResult`

### `aggregation`

- Responsibility:
  - combine judge outputs into a global result
  - enforce blocker rules and weighting
- Inputs:
  - all `JudgeResult` objects
  - aggregation policy from `rules`
- Outputs:
  - overall score, status, summary, and prioritized findings

### `adapters.sources`

- Responsibility:
  - isolate source validation interactions from core business logic
  - perform URL, domain, or metadata checks as needed
- Inputs:
  - extracted sources or source references
- Outputs:
  - normalized source-validation facts for the sources judge

### `observability`

- Responsibility:
  - logging
  - metrics
  - auditability
  - trace correlation
- Inputs:
  - events emitted during request processing
- Outputs:
  - operational signals for monitoring and debugging

### `ui`

- Responsibility:
  - provide a demo and review surface for the backend
  - submit evaluation payloads manually
  - display backend status and responses
- Inputs:
  - backend base URL
  - user-entered evaluation payloads
- Outputs:
  - client-facing progress view
  - backend request and response visualization

## End-to-End Data Flow

### Current Implemented Flow

```text
User -> Streamlit UI -> FastAPI endpoint -> Placeholder response -> UI console
```

This flow is already available for demos and manual testing.

### Step 1: Request Intake

- The client submits content and evaluation metadata.
- The transport layer validates the request shape and required fields.
- The system builds an internal `EvaluationRequest`.

### Step 2: Rule Resolution

- The application layer resolves the active rule profile.
- The profile determines:
  - which judges run
  - which rules apply
  - how results are weighted
  - which failures are blocking

### Step 3: Preprocessing

- The raw content is normalized into a canonical representation.
- Structural signals are extracted once, for example:
  - title
  - headings
  - paragraphs
  - links
  - source references
  - CTA markers
  - keyword presence
  - word and character counts
- The output becomes `PreprocessedContent`.

### Step 4: Judge Execution

- The orchestrator selects the enabled mini-judges.
- Each judge evaluates one dimension independently.
- Each judge returns a `JudgeResult` with:
  - status
  - score
  - finding list
  - rule references
  - evidence

### Step 5: Aggregation

- The aggregator combines all `JudgeResult` objects.
- Blocking failures are applied first.
- If no blocker fails, the global score is calculated from judge weights.
- The aggregator also creates the top-level summary and prioritized issues.

### Step 6: Response Construction

- The response builder assembles the final `EvaluationResponse`.
- The client receives:
  - overall decision
  - aggregate score
  - dimension-by-dimension results
  - explainable findings
  - relevant metadata

## Core Domain Objects

### `EvaluationRequest`

- Role: canonical input for one evaluation run.
- Contains:
  - content to evaluate
  - metadata such as content type or channel
  - keyword list
  - source references
  - selected rule profile
  - evaluation options

### `PreprocessedContent`

- Role: shared fact base derived from raw input.
- Contains normalized and extracted signals used by all judges.
- Prevents repeated parsing and encourages consistency across dimensions.

### `JudgeResult`

- Role: output of one mini-judge.
- Should capture:
  - evaluated dimension
  - pass or fail style status
  - dimension score
  - findings
  - evidence
  - rule identifiers
  - severity or criticality impact

### `EvaluationResponse`

- Role: final client-facing evaluation result.
- Should contain:
  - overall decision
  - aggregate score
  - per-dimension results
  - summary findings
  - traceable metadata such as profile or rule version

## Mini-Judge Architecture

### Design Goals

- One judge per evaluation dimension.
- Shared input contract across all judges.
- Independent execution and isolated reasoning.
- Clear extension point for new dimensions.

### Judge Contract

Each judge should conceptually:

- receive `PreprocessedContent`
- receive the rules relevant to its dimension
- evaluate only its assigned concern
- emit one `JudgeResult`

### Why This Works Well in V1

- Simple mental model for developers
- Easy to test each dimension in isolation
- Easy to disable or replace one judge without affecting others
- Supports future parallel execution if needed

### Orchestration Strategy

- Use a registry of enabled judges rather than hard-coding logic in one large
  evaluator.
- Let the orchestrator:
  - discover the enabled judges for the profile
  - execute them in a predictable order
  - collect outputs uniformly
- Keep the orchestrator procedural and lightweight.

## Aggregation Strategy

Aggregation should produce both a decision and an explanation.

### Recommended Approach

- Evaluate all enabled judges.
- Check for blocking rule failures first.
- If any blocking rule fails, overall status becomes `fail`.
- If no blocker fails, compute the overall score from judge weights.
- Preserve all per-dimension details even when the top-level result is already
  failed.

### Criticality Model

Use simple V1 levels:

- `blocking`: failure means automatic top-level failure
- `major`: strongly impacts score and summary priority
- `minor`: affects score and reporting, but not top-level viability alone

### Scoring Guidance

- Keep scoring readable rather than mathematically sophisticated.
- Weight at the judge level in V1, not at many nested sublevels.
- Exclude `not_applicable` dimensions from the weighted denominator.
- Represent `unknown` separately so temporary adapter issues do not masquerade as
  compliant results.

## Architectural Principles

### Modularity

- Each module owns one concern.
- Each judge owns one dimension.
- Adapters isolate infrastructure-specific behavior.

### Separation of Concerns

- Transport handles requests and responses.
- Application coordinates workflow.
- Domain defines semantics.
- Judges evaluate rules.
- Aggregation decides the final outcome.

### Extensibility

- Add a new judge by registering it and defining its rule set.
- Add a new profile without changing evaluation flow.
- Swap infrastructure adapters without modifying domain logic.

### Testability

- Preprocessing can be tested independently from judges.
- Each judge can be tested against fixed `PreprocessedContent`.
- Aggregation can be tested with synthetic `JudgeResult` inputs.
- End-to-end tests can validate the request-to-response workflow.

### Explainability

- Every finding should link back to a rule identifier.
- Every failure should include enough evidence to be actionable.
- The response should preserve both high-level and per-dimension detail.

## V1 vs Future Evolution

### V1

- synchronous evaluation API
- deterministic rule-based evaluation only
- one shared preprocessing stage
- modular mini-judge architecture
- weighted aggregation with blocker support
- explainable response payload
- basic source validation adapter
- Streamlit UI for review and client-facing demonstrations

### Later

- semantic quality evaluation
- deeper causal explanations
- correction or rewrite suggestions
- confidence modeling
- ML-assisted scoring or ranking
- preference learning
- asynchronous batch processing
- richer analytics and rule governance tools

## Recommended Non-Goals for V1

To avoid over-engineering, V1 should not include:

- distributed judge execution
- event-driven pipelines
- rule authoring UI
- database persistence for historical analytics
- workflow engines
- ML model serving infrastructure

## Summary

The recommended architecture is a small, service-oriented backend with:

- a thin API layer
- one central evaluation application service
- a shared preprocessing pipeline
- modular mini-judges by dimension
- a separate aggregation layer
- explicit rule profiles and criticality

This keeps the system maintainable today and easy to extend tomorrow.
