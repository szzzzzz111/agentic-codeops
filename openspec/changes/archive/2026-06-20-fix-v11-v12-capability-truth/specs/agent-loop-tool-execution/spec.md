## MODIFIED Requirements

### Requirement: Capability Status Reflects Current Runtime Truth

系统 SHALL ensure capability-status answers describe the currently implemented runtime rather than historical
stage non-goals. A capability-status answer MUST NOT claim an archived implemented capability is unavailable.

A patch capability-status answer MUST acknowledge implemented Safe Patch Authoring, Verification Runner,
Patch + Verify, Persistent Audit / Recovery, and the retained-worktree lifecycle through disposal/reconciliation.
It MUST continue to distinguish current non-goals, including verified patch promotion, automatic commit,
automatic push, and default real patch-diff generation.

A Grounded Answer / Model Provider capability-status answer MUST acknowledge that deterministic query rewrite,
deterministic rerank, and Memory were implemented by later archived stages. A Query Rewrite / Rerank
capability-status answer MUST acknowledge implemented Memory. These answers MUST distinguish deterministic
rewrite/rerank from unimplemented real LLM rewrite/rerank, and implemented Memory from unimplemented vector memory,
automatic memory summarization, cross-repository intelligent recall, and context compression.

Capability-status requests MUST NOT call repo RAG or perform patch, verification, worktree, memory, or long-task
mutation. The existing best-effort V19 trace envelope MAY still be persisted.

#### Scenario: Patch capability status includes current lifecycle

- **WHEN** the user asks whether patch support is implemented
- **THEN** the answer identifies the implemented patch, verification, audit, and worktree lifecycle boundaries
- **AND** it does not claim Persistent Audit / Recovery or Worktree Isolation is unimplemented
- **AND** `related_files` and `tool_calls` remain empty

#### Scenario: Patch capability status preserves current non-goals

- **WHEN** the system returns patch capability status
- **THEN** the answer states that verified promotion and automatic commit/push are not implemented
- **AND** it does not imply that the default application can generate a real patch diff

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
