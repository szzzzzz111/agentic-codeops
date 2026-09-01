# real-agent-observability-qualification Specification

## Purpose

定义 RepoPilot 在扩展 Coding Agent supervisor 之前的最小真实可观察性资格边界：必须从真实 Agent 事件中
fail-closed 地取得唯一终态与完成声明，并让独立验证回执绑定终态后的同一 Git snapshot；该资格不证明语义完成、
产品验收或 supervisor runtime 已实现。

## Requirements
### Requirement: Real Agent Completion Is Observed Fail Closed

The qualification validator SHALL accept only an actual captured Codex CLI JSONL event stream with one thread start,
one turn start, a final Agent message containing the exact `READY_FOR_REVIEW` completion claim, and one terminal
`turn.completed` event that is last. Missing, malformed, duplicated, conflicting or out-of-order required events SHALL
produce `NOT_OBSERVED`. Synthetic test fixtures MAY validate parser behavior but MUST NOT be reported as real qualification
evidence. A completion claim SHALL initiate verification and MUST NOT be treated as semantic completion or acceptance.

#### Scenario: Terminal event is missing

- **WHEN** the captured real Agent stream has no `turn.completed`
- **THEN** qualification returns `NOT_OBSERVED`

#### Scenario: Completion claim is missing

- **WHEN** no final Agent message before the terminal event is exactly `READY_FOR_REVIEW`
- **THEN** qualification returns `NOT_OBSERVED`

#### Scenario: Event chronology is ambiguous

- **WHEN** the stream has multiple terminal events or any event after the terminal event
- **THEN** qualification returns `NOT_OBSERVED`

### Requirement: Verification Receipt Is Bound To The Completion Snapshot

The qualification input SHALL include a clean baseline Git snapshot, an Agent-completion snapshot, and a verification
receipt. Canonical snapshot identity SHALL bind repository id, HEAD, status digest, tracked binary diff digest and untracked
inventory digest. Qualification snapshots MUST reject any non-empty untracked inventory. The completion snapshot MUST use
the same repository id and HEAD as baseline and MUST differ from the clean baseline. The receipt MUST record a
non-empty deterministic command, exit code zero, the canonical completion snapshot SHA256 and the complete
post-verification snapshot. The validator SHALL recompute the latter's canonical SHA256 and require it to equal the
completion snapshot; a caller-supplied post-verification hash alone MUST NOT satisfy the binding. Missing fields, dirty
baseline, nonzero verification or any snapshot mismatch SHALL produce `NOT_OBSERVED`.

#### Scenario: Fixture baseline is dirty

- **WHEN** the baseline snapshot records `clean=false`
- **THEN** qualification returns `NOT_OBSERVED`

#### Scenario: Verification fails

- **WHEN** the receipt records a nonzero verification exit code
- **THEN** qualification returns `NOT_OBSERVED`

#### Scenario: Receipt is not bound to the same snapshot

- **WHEN** the bound snapshot differs from the completion snapshot or the post-verification snapshot changes
- **THEN** qualification returns `NOT_OBSERVED`

#### Scenario: Real run is mechanically qualified

- **WHEN** the real event sequence is unique and ordered, baseline is clean, the Agent produced a changed completion
  snapshot, verification exits zero, and the receipt binds the unchanged completion snapshot
- **THEN** qualification returns `QUALIFIED_OBSERVABILITY`
- **AND** the report states that semantic correctness, product acceptance, supervisor runtime and Git delivery remain unproved
