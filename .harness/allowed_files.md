# 当前 Harness 写入边界

Active OpenSpec change：none。`add-governed-run-contract` 已归档到
`openspec/changes/archive/2026-09-01-add-governed-run-contract/`。

Planning base 与 authorized remote tip：
`cf2679b9fc96e54cfb7a665ff7c0a4aaf05b9dd0`（`origin/main`）。

Risk：high / L3。该阶段新增内部 runtime 监督合同、只读 Git snapshot collector、真实 Codex JSONL
事件适配和人工 review 决策语义；不新增公开 API、持久化 authority、Agent launcher 或任何仓库写入/自动 Git 交付。

Action ceiling：push。用户已直接授权本阶段完成 archive、finite candidate commit、ff-only merge，
并以 `cf2679b9fc96e54cfb7a665ff7c0a4aaf05b9dd0` 为精确 old-tip lease 显式 push 到 `origin/main`。

## 已冻结的 semantic subject

归档后 semantic subject 以
`.harness/reviews/add-governed-run-contract/implementation/reviewed-change-manifest.json`
中的最终 post-archive changes 为精确清单。该清单绑定内部监督 kernel/tests、归档 OpenSpec、长期 spec、
durable docs、authority epochs、Harness final state 与 plan review set；manifest、inventory、本文件和 review
checklist 在最终 packet 冻结后不得再改。

归档目录 `openspec/changes/archive/2026-09-01-add-governed-run-contract/` 只保存 OpenSpec archive
生成的历史，不得追加改写。

## 唯一 evidence tail

最终 post-archive packet 冻结后，只允许 controller 写入：

- `.harness/reviews/add-governed-run-contract/implementation/review-set.json`
- `.harness/authority/add-governed-run-contract/delivery-binding.json`

除此之外一律停止写入。两席 review-set 只绑定最终 packet；delivery binding 只绑定该 packet、最终 Harness
文件与 current authority，不得扩大 scope、runtime 能力或产品 claim。

## 明确禁止

- 不写原脏 worktree `/Users/chelaile/agentic-codeops`。
- 不新增或修改 `/chat`、CLI 命令、public response schema、ToolRegistry route 或默认 provider。
- 不由 RepoPilot 启动真实 Agent，不新增 daemon、background worker、runtime subagent、通知或 retry loop。
- 不实现持久化 Operator identity/approval；`READY_FOR_REVIEW` 只表示等待人工 review，绝不表示完成。
- RepoPilot runtime 不自动 apply、repair、rollback、commit、merge、push、建 branch/PR 或修改 Agent worktree。
- 不把 fake/mock 事件当作真实运行证据，不把 contract evaluator PASS 写成产品验收。
- 不修改上一阶段的 qualification validator、既有 qualification tests 或长期 qualification spec；仅可只读消费。
- 不创建第二个 product stage；archive/commit/merge/push 只用于当前阶段的 finite closeout。
- 不采用非 ff-only 合并，不向 `origin/main` 之外推送，不弱化精确 old-tip lease。

## Stop conditions

- 需要把 public API、持久化 authority、Agent launcher、任意 shell、动态 argv 或仓库写入开放为
  RepoPilot runtime 能力。
- 不能用 child-env allowlist、无 repository-controlled helper、固定 argv、`shell=False`、有界执行和双稳定采样捕获
  可重算 endpoint snapshot，或实现需要声称排除了完美 ABA/全过程并发写入。
- 事件终态/claim、changed-path scope 或 verification receipt 无法绑定同一 snapshot。
- 需要修改 allowlist 外路径、原脏 worktree，或执行当前 finite closeout 之外的 Git mutation。
- remote、target branch、planning base、risk、scope 或 required review slot 发生漂移。
- 最终 packet、candidate index、delivery binding、local/remote main 或 same-endpoint 对账不一致。
