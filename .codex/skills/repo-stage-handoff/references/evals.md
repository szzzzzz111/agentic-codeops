# Repo Stage Handoff Evals

Use these as routing and behavior checks after changing the skill.

## Positive

- Query: `V19 已经 merge/push 了，检查交接文档是不是还准确。`
  - Expect: load this skill; verify main/remote/feature branch state, durable-doc parity, validation evidence, and retention decision.
- Query: `准备换会话，帮我更新 HANDOFF 和 PROGRESS。`
  - Expect: load this skill; update stable next-session state and run Stage Debt Sweep.

## Negative

- Query: `帮我实现 audit store。`
  - Expect: do not load this skill as the primary workflow; this is implementation work.
- Query: `解释一下 README 里的架构图。`
  - Expect: do not run stage closeout unless the user also questions document freshness.

## Edge

- Query: `都合并了，还有没有文档没同步？`
  - Expect: load this skill; check positive parity by README responsibility area, not only stale-phrase absence.
- Query: `main 和远端 hash 一样，应该没问题了吧？`
  - Expect: load this skill; still inspect active changes, archive state, tests/checkers that lock stale docs, and branch retention.

## Failure Traps

- Do not treat a version mention in README snapshot as full parity.
- Do not write an exact current-HEAD claim inside the uncommitted docs update that will create a newer commit.
- Do not stop after docs grep; run closeout and full verification after parity/test/checker changes.
- Passing docs scans and closeout scripts do not prove semantic parity or actual branch/remote/handoff truth.

## Manual Judgment Cases

- Query: `closeout 脚本过了，handoff 肯定没问题。`
  - Expect: manually compare durable docs with actual Git/archive/remote state before concluding.
