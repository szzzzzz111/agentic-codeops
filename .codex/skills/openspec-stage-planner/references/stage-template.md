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

- Current behavior
- Target behavior
- Non-goals
- Data returned and not returned
- Error behavior
- Security and path boundaries
- Trace/audit implications if relevant

## Planning Manual Judgment Gates

Before implementation confirmation, record visible conclusions for:

- stage intent/scope and confirmation boundary
- safety/architecture and fail-closed behavior
- planned test adequacy for requirements, non-goals, errors, and security
- internal review findings and external feedback triage approach
- semantic parity targets across durable docs, Harness, and specs
- archive/merge/handoff risks to verify at closeout

OpenSpec validation checks artifact structure; it does not prove these judgments are correct.

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

- [ ] 4.1 Update README/PROGRESS/HANDOFF as needed.
- [ ] 4.2 Run `openspec validate <change>`.
- [ ] 4.3 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [ ] 4.4 Run `git diff --check`.
```

## Scope Smell Tests

Split the stage if it includes more than one of:

- new runtime API behavior
- new persistence or audit model
- new skill execution behavior
- new agent decision logic
- new permission, approval, or sandbox policy
