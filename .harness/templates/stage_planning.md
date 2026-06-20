# Stage Planning Template

用于创建 OpenSpec change 前的轻量规划。按风险填写，不把所有文档和 gate 机械复制进每个阶段。

## Stage

- Name: `<Vx or process-only name>`
- Branch/worktree: `<name>`
- Risk: `<low / medium / high>`
- Risk reason: `<blast radius, uncertainty, security or persistence boundary>`
- Previous baseline: `<completed stage>`

## Intent And Scope

- Problem: `<current gap>`
- Outcome: `<observable result>`
- In scope: `<small vertical slice>`
- Non-goals: `<explicit exclusions>`
- Public/runtime contract: `<unchanged or exact change>`

## Boundaries And Failures

- Owned modules/state: `<paths and stores>`
- Trust boundaries: `<identity, path, permission, lifecycle, content>`
- Failure behavior: `<fail closed, retry, rollback, partial state>`
- Audit/privacy implications: `<none or exact fields>`

## TDD And Verification

- First RED cases: `<tests and expected failure>`
- Positive/negative/safety cases: `<brief matrix>`
- Focused verification: `<commands>`
- Full verification trigger: `<runtime/tests changed or not>`

## Review Plan

- Internal review target: `<highest-risk assumptions>`
- External review: `<required / optional / not requested>`
- Independent counterexamples requested: `<failure modes>`
- Stage Debt Sweep paths: `<changed and directly dependent older paths>`

## Files And Durable Facts

- Allowed files: `<paths>`
- Review checklist additions: `<gates>`
- Durable docs whose owned facts change: `<paths or none>`
- Facts intentionally queried live: `<branch / HEAD / remote / active change>`

## Human Confirmation

- Internal plan review: `<findings closed / blockers>`
- Decision: `<goal, non-goals or sequence question>`
- Recommendation: `<one option and reason>`
- Implementation starts only after: `<confirmation>`
