## MODIFIED Requirements

### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL provide a lightweight Agent Harness Kernel to orchestrate request routing, Memory boundaries, Long Task boundaries, Assistant Control Surface, Patch command / Patch intent, Verification intent, Persistent Audit / Recovery intent, tool metadata, tool calls, grounded answer boundaries, and trace events.

The fixed front-of-loop order SHALL be:

1. memory command
2. long task command
3. assistant control surface
4. patch command / patch intent
5. verification intent
6. audit recovery/status intent
7. capability/status intent
8. `RequestRouter` repo_search/chat_only fallback

Audit recovery/status intent MUST be handled after patch and verification intent so execution confirmations are not swallowed. Audit recovery/status intent MUST be handled before repo_search so recovery questions do not trigger repo RAG.

#### Scenario: Recovery intent does not call repo RAG

- **WHEN** the chat message is a recovery/status request such as recent audit records, recovery status, recent verification result, trace lookup, or patch lookup
- **THEN** AgentLoop MUST handle it before `RequestRouter`
- **AND** AgentLoop MUST NOT call `repo_rag`
- **AND** AgentLoop MUST NOT treat the request as capability-status unless the recovery parser does not match

#### Scenario: Patch and verification intents still outrank recovery

- **WHEN** the chat message is a patch confirmation, patch proposal, combined patch/verify confirmation, or explicit verification request
- **THEN** AgentLoop MUST handle that execution intent before checking recovery/status intent

### Requirement: Kernel Records Persistent Audit Events

系统 SHALL attempt to record persistent audit summaries for each `/chat` trace envelope and for patch, verification, and long task events. Persistent audit recording MUST be best-effort and MUST NOT change the primary AgentLoop result if audit writing fails.

#### Scenario: Trace envelope is persisted for chat requests

- **WHEN** AgentLoop handles a `/chat` request
- **THEN** AgentLoop SHOULD record a lightweight trace envelope containing safe route/status/tool-count information
- **AND** the persisted envelope MUST NOT include full answer text, full trace, local absolute paths, or secrets

#### Scenario: Audit write failure preserves AgentLoop result

- **WHEN** persistent audit recording fails
- **THEN** AgentLoop returns the same public answer, related files, and tool call summaries as the primary path would return without audit persistence
