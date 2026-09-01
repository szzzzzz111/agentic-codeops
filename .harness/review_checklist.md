# 当前 Review 清单

Active OpenSpec change：none。`qualify-real-agent-observability` 已归档；semantic subject 将由最终
post-archive manifest 冻结，随后只允许 review-set 与 delivery-binding 两个 evidence tail。

Risk：low；开发期 qualification validator/tests + controller 显式真实 Codex fixture probe。
Authority 绑定 plan/implementation 各 0 个 independent slots，但仍要求完整 plan packet、一次内部计划复核、
activation/authority/allowlist/hash preflight 和确定性验证。零槽不等于产品验收或 supervisor 已完成。

## Freeze And Plan

- [x] Live `origin/main`、target、remote endpoints 和 planning base 已复核。
- [x] 从 `3e884a9725b0ca715d236fb2431ca058db51912b` 建立独立干净 worktree；原脏 worktree 只读。
- [x] Scope 只包含真实事件入口、干净 fixture、Git snapshot、completion claim、verification receipt、
  六类故障与 stop conditions。
- [x] 一次内部计划复核无 P0/P1，plan packet 和 authority implement preflight 通过。

## TDD And Qualification

- [x] RED：缺终态、缺 completion claim、事件歧义/乱序、dirty baseline、verification nonzero、
  receipt/snapshot mismatch 六类故障均 fail closed。
- [x] GREEN：validator 只接受唯一 `turn.completed`、终态前精确 `READY_FOR_REVIEW` claim、干净 baseline、
  有变化的 completion snapshot、exit 0 receipt 和 verification 前后同一 snapshot。
- [x] 真实 Codex CLI 在新建临时 Git fixture 中产生实际 Agent 事件和未提交代码变化；不把测试 fixture 当真证据。
- [x] Controller 在 Agent 终态后捕获 snapshot，独立运行 fixture verifier，再捕获同一 snapshot 并生成 receipt。
- [x] 资格结果为 `QUALIFIED_OBSERVABILITY` 或 `NOT_OBSERVED`；不声称语义完成、产品验收或 supervisor MVP。

## Verification And Stop

- [x] Internal implementation review 修复两个 binding findings：post-verification snapshot 由 validator 重算，
  且 snapshot 明确绑定 tracked binary diff 并拒绝任何 untracked path；focused `10 passed`。
- [x] Focused Stage Debt Sweep 覆盖 validator/tests、active OpenSpec、Harness、PROGRESS/HANDOFF 及关键词直接依赖；
  未发现 `app/**`、subprocess/Git mutation、fake-as-real 或越权交付残留。
- [x] Final canonical verification：`1062 passed`；full Ruff、stage-doc、skill-eval 均 PASS。
- [x] OpenSpec 1.3.1 active strict PASS、`validate --all` 25/25；authority/allowlist、JSON/report replay 和
  `git diff --check` 通过。
- [x] 若 terminal/claim 或 snapshot-bound receipt 任一不成立，结果必须 `NOT_OBSERVED`，并停止 supervisor 后续开发。
- [x] 最终报告列出真实证据、claim ceiling、未知项和下一步建议。

## Archive And Delivery

- [x] Archive authority preflight PASS；change 已同步长期 spec 并归档到
  `2026-09-01-qualify-real-agent-observability`。
- [x] Archive 前完整验证仍为 `1062 passed`，Ruff、stage-doc、skill-eval 全绿；focused `10 passed`。
- [ ] Final zero-slot implementation packet、review-set 与 delivery-binding mechanical PASS。
- [ ] Staged index 与 reviewed packet 精确一致，并创建 planning base 的单一 candidate。
- [ ] Controller-only ff-only 合并，使用 explicit refspec + exact-old-OID lease push，并从同 endpoint 对账。
