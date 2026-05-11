## ADDED Requirements

### Requirement: Agent loop uses deterministic keyword search

The system SHALL use a minimal deterministic keyword extraction rule for the current `CodeAgent` behavior and MUST NOT require a real LLM.

#### Scenario: Search token in message

- **WHEN** a chat message contains an explicit searchable token such as `UNIQUE_BUG_TOKEN`
- **THEN** the Agent uses that token as the search keyword

### Requirement: Tool calls go through ToolExecutor

The system SHALL route Agent repository search through `ToolExecutor` before calling concrete file tools.

#### Scenario: Search tool invocation

- **WHEN** `CodeAgent` performs repository search for `/chat`
- **THEN** it invokes `search_code` through `ToolExecutor`

### Requirement: Chat returns related files from real search results

The system SHALL populate `related_files` from safe search results and keep the response stable when no files match.

#### Scenario: Search hit

- **WHEN** safe repository search finds matching files
- **THEN** `/chat` returns unique relative file paths in `related_files`

#### Scenario: No search hit

- **WHEN** safe repository search finds no matching files
- **THEN** `/chat` returns an empty `related_files` list and remains successful

### Requirement: Tool call summaries are safe

The system SHALL return tool call summaries that include tool name, parameter summary, status, and result count without leaking full file content, complete search results, or local absolute paths.

#### Scenario: Search call summary

- **WHEN** `/chat` invokes repository search
- **THEN** `tool_calls` includes a `search_code` summary with keyword, status, and result count
- **AND** it does not include full file content or local absolute paths

### Requirement: Agent loop excludes future high-risk capabilities

The current Agent loop MUST NOT modify code, execute shell commands, use RAG, use Memory, perform Reflection, run evals, or use complex multi-Agent orchestration.

#### Scenario: Current chat behavior

- **WHEN** a user sends a chat request
- **THEN** the system performs only the current read-only search behavior
