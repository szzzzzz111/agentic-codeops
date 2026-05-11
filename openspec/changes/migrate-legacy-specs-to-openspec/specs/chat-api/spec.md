## ADDED Requirements

### Requirement: Chat endpoint accepts traceable requests

The system SHALL expose `POST /chat` as the Agent service entrypoint. Requests MUST include `user_id`, `session_id`, `message`, and `repo_path`.

#### Scenario: Valid chat request

- **WHEN** a client sends a valid `POST /chat` request with `user_id`, `session_id`, `message`, and `repo_path`
- **THEN** the system returns a successful response using the stable chat response schema

### Requirement: Chat response includes audit fields

The system SHALL return `trace_id`, `answer`, `related_files`, and `tool_calls` in every successful chat response.

#### Scenario: Trace response shape

- **WHEN** a chat request completes successfully
- **THEN** the response includes a `trace_id` beginning with `trace_`
- **AND** the response includes `answer`, `related_files`, and `tool_calls`

### Requirement: Trace identifiers are unique per request

The system SHALL generate a distinct request-level `trace_id` for each chat request.

#### Scenario: Consecutive requests

- **WHEN** two chat requests are sent consecutively
- **THEN** their `trace_id` values are different

### Requirement: API layer stays thin

The API layer MUST expose HTTP routing and schema handling without directly implementing repository search, tool execution, or Agent decisions.

#### Scenario: Chat orchestration boundary

- **WHEN** `/chat` handles a request
- **THEN** request orchestration goes through the service and Agent layers instead of embedding tool logic in the router
