# 当前 Harness 写入边界

Active OpenSpec change：none。`qualify-real-agent-observability` 已归档到
`openspec/changes/archive/2026-09-01-qualify-real-agent-observability/`。

Planning base 与 authorized remote tip：
`3e884a9725b0ca715d236fb2431ca058db51912b`（`origin/main`）。

Risk：low。该阶段只增加开发期 qualification validator、确定性测试、一次真实 Codex CLI
fixture 观测及对应阶段文档；不修改 `app/**`、runtime/public contract、默认 provider、权限、持久化、
依赖或网络默认行为。真实 Agent 调用由 controller 在临时 fixture 中显式发起，不成为 RepoPilot runtime。

Action ceiling：push。用户已直接授权本阶段 candidate commit、ff-only 合并和以
`3e884a9725b0ca715d236fb2431ca058db51912b` 为精确 lease 的 `origin/main` push；授权只覆盖本阶段必要收口。

## 已冻结的 semantic subject

归档后 semantic subject 以
`.harness/reviews/qualify-real-agent-observability/implementation/reviewed-change-manifest.json`
中的最终 post-archive changes 为精确清单。该清单绑定 qualification validator/tests、真实 observation/report、
归档 OpenSpec、长期 spec/index、durable progress/handoff、authority epochs 与 plan review set；manifest、inventory、
本文件和 review checklist 在最终 packet 冻结后不得再改。

归档目录 `openspec/changes/archive/2026-09-01-qualify-real-agent-observability/` 只保存 OpenSpec archive
生成的历史，不得追加改写。

## 唯一 evidence tail

最终 post-archive packet 冻结后，只允许 controller 写入：

- `.harness/reviews/qualify-real-agent-observability/implementation/review-set.json`
- `.harness/authority/qualify-real-agent-observability/delivery-binding.json`

除此之外一律停止写入。零槽 review-set 只绑定最终 packet；delivery binding 只绑定该 packet、最终 Harness
文件与 authority，不得扩大 scope 或产品 claim。

## 明确禁止

- 不写原脏 worktree `/Users/chelaile/agentic-codeops`。
- 不修改 `app/**`，不新增 RepoPilot runtime subprocess/provider/supervisor 行为。
- 不用 fake、mock 或手写事件冒充真实 Agent 资格证据。
- 不扩展到 UI、daemon、多 Agent、通知、自动纠偏或 RepoPilot runtime 自动 apply/commit/merge/push。
- 不顺带开始 governed run contract 或其他下一阶段。
- 不采用非 ff-only 合并，不向 `origin/main` 之外的 ref 推送，不弱化精确 lease。

## Stop conditions

- 最终 packet、candidate index、delivery binding 或 qualification evidence 任一不一致。
- remote endpoint、local/remote `main`、candidate、测试、归档状态或 authorized old tip 漂移。
- 需要写原脏 worktree、最终 manifest/evidence tail 外路径，或需要本阶段收口之外的 commit/merge/push。
