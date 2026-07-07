## MODIFIED Requirements

### Requirement: Capability Status Reflects Current Runtime Truth

系统 SHALL ensure capability-status answers describe the currently available runtime primitives and the implemented product boundaries rather than historical stage non-goals. A capability-status answer MUST NOT claim an archived implemented capability is unavailable, and MUST NOT claim an execution capability is currently available when its required backing runtime primitive is absent from the active `ToolRegistry`.

Capability-status availability SHALL be derived from a small internal capability status adapter that consumes `ToolRegistry` metadata and fixed safety boundaries. `ToolRegistry` MAY expose a read-only snapshot/list of registered `ToolSpec` values, but MUST NOT dispatch tools or own user-facing product wording.

A patch capability-status answer MUST acknowledge implemented Safe Patch Authoring, Verification Runner, Patch + Verify, Persistent Audit / Recovery, retained-worktree lifecycle through disposal/reconciliation, and Verified Patch Promotion according to the active runtime. Execution subcapabilities such as patch apply, verification run and worktree creation/disposal MUST be backed by the required active `ToolRegistry` primitives before they are described as currently available. Verified Patch Promotion is a composed subcapability: it does not require a dedicated promotion tool, but MUST be described only when the active runtime has the required promotion route/preflight and the backing primitive(s) used for the main-workspace write path. Manager-only subcapabilities such as Persistent Audit / Recovery MAY be described from fixed runtime manager wiring and safety boundaries. It MUST continue to distinguish current non-goals, including automatic commit, automatic push, branch/PR automation, connector, background retry, runtime subagent, and default real patch-diff generation.

A Grounded Answer / Model Provider capability-status answer MUST acknowledge deterministic query rewrite, deterministic rerank, and Memory as implemented runtime/product boundaries. A Query Rewrite / Rerank capability-status answer MUST acknowledge implemented Memory. These answers MUST distinguish deterministic rewrite/rerank from unimplemented real LLM rewrite/rerank, and implemented Memory from unimplemented vector memory, automatic memory summarization, cross-repository intelligent recall, and context compression.

Capability-status requests MUST NOT call repo RAG or perform patch, verification, worktree, memory, or long-task mutation. The existing best-effort V19 trace envelope MAY still be persisted.

#### Scenario: Default patch capability status includes current lifecycle

- **WHEN** the user asks whether patch support is implemented
- **THEN** the answer identifies the implemented patch, verification, audit, worktree lifecycle and verified promotion boundaries
- **AND** it does not claim Persistent Audit / Recovery, Worktree Isolation or Verified Patch Promotion is unimplemented
- **AND** `related_files` and `tool_calls` remain empty

#### Scenario: Patch capability status preserves current non-goals

- **WHEN** the system returns patch capability status
- **THEN** the answer distinguishes controlled verified promotion from unimplemented automatic commit/push, branch/PR automation, connector, background retry and runtime subagent behavior
- **AND** it does not imply that the default application can generate a real patch diff

#### Scenario: Missing backing primitive is not advertised as available

- **WHEN** a capability-status request is handled by an AgentLoop whose active `ToolRegistry` does not contain a required backing primitive such as `patch_apply` or `verification_run`
- **THEN** the answer MUST NOT describe that missing execution path as currently available
- **AND** the answer MAY state that the runtime primitive is not registered in the current loop
- **AND** the request MUST NOT call repo RAG or any write-risk tool

#### Scenario: Grounded answer status reflects later rewrite and memory capabilities

- **WHEN** the user asks whether Grounded Answer or Model Provider is implemented
- **THEN** the answer acknowledges deterministic query rewrite, deterministic rerank, and Memory
- **AND** it does not claim those archived capabilities are unavailable
- **AND** it preserves current real LLM, vector memory, and context compression non-goals

#### Scenario: Rewrite and rerank status reflects later memory capability

- **WHEN** the user asks whether query rewrite or rerank is implemented
- **THEN** the answer acknowledges deterministic query rewrite, deterministic rerank, and Memory
- **AND** it distinguishes them from real LLM rewrite/rerank and vector memory
- **AND** `related_files` and `tool_calls` remain empty
