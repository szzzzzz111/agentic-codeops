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
7. `RequestRouter` capability_status / repo_search / chat_only fallback

Capability/status routing SHALL remain inside `RequestRouter` and SHALL be determined by an internal deterministic classifier or helper, not by duplicating ad hoc route strings at each call site. The classifier/helper MUST preserve existing route output, MUST NOT be hoisted ahead of AgentLoop pre-router routes, and MUST NOT expand Assistant Control Surface status triggers.

Audit recovery/status intent MUST be handled after patch and verification intent so execution confirmations are not swallowed. Audit recovery/status intent MUST be handled before repo_search so recovery questions do not trigger repo RAG.

#### Scenario: Recovery intent does not call repo RAG

- **WHEN** the chat message is a recovery/status request such as recent audit records, recovery status, recent verification result, trace lookup, or patch lookup
- **THEN** AgentLoop MUST handle it before `RequestRouter`
- **AND** AgentLoop MUST NOT call `repo_rag`
- **AND** AgentLoop MUST NOT treat the request as capability-status unless the recovery parser does not match

#### Scenario: Patch and verification intents still outrank recovery

- **WHEN** the chat message is a patch confirmation, patch proposal, combined patch/verify confirmation, or explicit verification request
- **THEN** AgentLoop MUST handle that execution intent before checking recovery/status intent

#### Scenario: Capability status classifier preserves route output

- **WHEN** the chat message asks whether a currently tracked capability is implemented or supported
- **THEN** `RequestRouter` MUST route it as `capability_status`
- **AND** the route keyword MUST remain `capability_status`
- **AND** the route reason MUST remain `capability_status_question`
- **AND** the request MUST NOT call `repo_rag`

#### Scenario: Search-like location questions are not swallowed by capability status

- **WHEN** the chat message contains capability vocabulary but asks where or how to locate code
- **THEN** the capability-status classifier MUST NOT classify it as a capability-status question
- **AND** `RequestRouter` MAY continue to route it as repo search when a searchable token exists
