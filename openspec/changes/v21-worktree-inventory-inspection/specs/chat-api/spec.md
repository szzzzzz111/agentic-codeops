## ADDED Requirements

### Requirement: Worktree Inventory And Inspection Reuse The Existing Chat Contract

系统 SHALL return V21 inventory and inspection through the existing `/chat.answer`. V21 MUST NOT add required or optional top-level `/chat` fields or a standalone worktree API.

`related_files` and `tool_calls` MUST remain empty for inventory / inspection because the flow does not use repo RAG or execution tools.

#### Scenario: Inspection answer keeps chat schema

- **WHEN** `/chat` returns a V21 inspection result
- **THEN** the response contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** bounded preview may appear only in `answer`
- **AND** `related_files` and `tool_calls` are empty
