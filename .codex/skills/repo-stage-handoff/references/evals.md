# Repo Stage Handoff Evals

## Positive

- Query: `阶段已经 archive、merge、push，做最终交接。`
  - Expect: verify live state and write one concise final handoff.
- Query: `准备换会话，只保留下一轮真正需要的信息。`
  - Expect: keep durable history in PROGRESS and current action context in
    HANDOFF.

## Negative

- Query: `帮我实现 audit store。`
  - Expect: use implementation workflow, not handoff.
- Query: `正式 review 这个 patch 生命周期修复。`
  - Expect: use `repo-stage-review-loop`.

## Edge

- Query: `main 和远端一致，把 hash 写进所有文档。`
  - Expect: reject duplicated volatile hashes; reference live Git commands.
- Query: `archive 后发现 runtime bug，顺手在交接里修掉。`
  - Expect: reopen review/archive readiness rather than treating it as docs
    cleanup.

## Failure Traps

- Do not create separate mandatory handoffs after archive, merge, push, and
  branch cleanup.
- Do not duplicate full stage history in HANDOFF.
- Do not claim exact current HEAD from inside a change that will create a newer
  commit.
- Do not start the next stage during closeout.
