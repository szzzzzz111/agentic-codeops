# Stage Template

## Proposal Shape

```markdown
## Why

<用户价值和当前缺口>

## What Changes

- <本阶段新增或修改的能力>
- <文档/测试/边界同步>
- <明确不做什么>

## Capabilities

### New Capabilities

- `<capability-name>`

### Modified Capabilities

- `<capability-name>`

## Impact

- Code: `<paths>`
- Tests: `<paths>`
- Docs: `<paths>`
```

## Design Checklist

- Risk level and reason
- Current behavior
- Target behavior
- Non-goals
- Data returned and not returned
- Error behavior
- Security and path boundaries
- Trace/audit implications if relevant
- Internal review target and external-review expectation

## Planning Judgment

Before implementation confirmation, explain the stage intent, non-goals, risk,
safety boundaries, planned RED cases, review target, and which durable facts
will change. OpenSpec validation checks structure; it does not prove these
judgments are correct.

## Tasks Checklist

Use TDD-shaped tasks:

```markdown
## 1. Harness

- [ ] 1.1 Update allowed files.
- [ ] 1.2 Update review checklist.

## 2. Tests

- [ ] 2.1 Add failing tests for the new behavior.

## 3. Implementation

- [ ] 3.1 Implement the smallest code change.

## 4. Docs and Verification

- [ ] 4.1 Update only documents whose owned facts changed.
- [ ] 4.2 Run `openspec validate <change>`.
- [ ] 4.3 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [ ] 4.4 Run `git diff --check`.
```

## Stage Authority Envelope

For a stage governed by the activated authority gate, record and present:

- exact stage id, authority epoch and authority-record SHA-256
- risk, canonical scope digest and exact planning-base commit
- ordered action ceiling: `plan`, `implement`, `commit`, `archive`, `merge`, or `push`
- remote name, effective fetch and push endpoint fingerprints, target branch, and authorized remote tip
- exact/prefix allowed-path rules plus canonical non-goals
- invalidation on any scope, non-goal, risk, base, action, endpoint, branch, or tip drift

The host retains these values from the live direct-user confirmation and passes
them back as validator inputs. Do not reconstruct expected inputs from the
repository record; the record proves mechanical consistency only and cannot
assert live human authority.

## Scope Smell Tests

Split the stage if it includes more than one of:

- new runtime API behavior
- new persistence or audit model
- new skill execution behavior
- new agent decision logic
- new permission, approval, or sandbox policy
