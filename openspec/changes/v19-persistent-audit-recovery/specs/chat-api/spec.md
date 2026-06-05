## MODIFIED Requirements

### Requirement: `/chat` Response Contract Remains Stable

系统 SHALL keep the existing `/chat` top-level response fields unchanged while adding V19 recovery/status behavior. Recovery/status answers MUST be returned through the existing `answer` field, with `related_files` and `tool_calls` preserving existing safe semantics.

V19 MUST NOT add a standalone audit API or new required/optional top-level `/chat` fields.

#### Scenario: Recovery answer uses existing contract

- **WHEN** the user asks for recent audit records or recovery status through `/chat`
- **THEN** the response still contains only the established top-level fields
- **AND** the recovery information is formatted in `answer`
- **AND** no full internal trace, DB path, full diff, full stdout/stderr, Evidence Pack, provider content, secret, or local absolute path is exposed
