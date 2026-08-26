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
- Authority activation state: `<not yet active / active with external activation evidence>`
- Authority cohort: `<pre-change v1 / externally activated v2; selected only by host chronology>`
- Host-retained authority inputs: `<stage, epoch, record hash, risk, scope digest, planning base, action ceiling, remote name, effective fetch/push endpoint fingerprints, target branch, authorized remote tip>`
- Replay activation status: `<dormant blocked_on_external_host_capability / activated by later reviewed host stage>`
- Replay host capability: `<provider_neutral.stage_state_cas/v1 evidence or explicitly unavailable>`
- Host-retained replay state (v2 only): `<immutable workspace binding, terminal state, gate snapshot generation/digest, event count/head, receipt count/head>`
- Replay current frontier/action mapping (v2 only): `<exact set and implement/archive/commit/merge/push mapping; no unaffected bypass>`
- Invalidation triggers: `<scope/non-goal/risk/base/action/endpoint/branch/tip drift>`
- Implementation starts only after: `<direct-user confirmation plus applicable mechanical/provenance/activation gates>`

Repository records and hashes are mechanical bindings only. They do not prove user identity, host-message authenticity,
activation chronology, or `human_authorized=true`; never populate host-retained expected inputs by reading them back from
the record being validated.

Replay reports/templates are also mechanical-only. The introducing and
already-in-flight v1 cohorts stay v1 through terminal and use later-v1 authority
replacement after authorized drift. Only a later independently reviewed
activation with real external host capability may create new v2 cohorts.
