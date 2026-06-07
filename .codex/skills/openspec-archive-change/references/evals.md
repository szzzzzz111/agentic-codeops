# OpenSpec Archive Change Evals

Use these as routing and behavior checks after changing the skill.

## Positive

- Query: `外部 review 没问题了，归档 v19-persistent-audit-recovery。`
  - Expect: load this skill; verify artifacts/tasks, assess delta sync, validate operation/header alignment, then archive.
- Query: `这个 OpenSpec change 已完成，请 finalize/archive。`
  - Expect: load this skill and archive the explicitly identified completed change.

## Negative

- Query: `开始实现 v20。`
  - Expect: do not load this skill.
- Query: `看看 active changes 有哪些。`
  - Expect: list/status only; do not archive without explicit archive/finalize intent.

## Edge

- Query: `继续下一步。`
  - Expect: do not guess archive intent unless the conversation clearly establishes archive as the approved next step.
- Query: `validate 通过了，直接 archive。`
  - Expect: still compare delta operation types and requirement headers; block new headers incorrectly placed under `MODIFIED`.
- Situation: archive aborts during spec sync.
  - Expect: confirm no files changed, repair delta classification, rerun strict validation, and retry; do not manually move a partial archive.

## Failure Traps

- Do not treat `openspec validate <change>` as proof that delta sync will apply.
- Do not archive on vague continuation language unless archive intent is already explicit.
- Do not manually move a change after archive sync aborts.
